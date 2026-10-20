"""Hash-based FTP deployment with parallel transfers and resumable checkpoints.

Uses only Python's standard library and the existing FTP_* GitHub secrets.
"""

import concurrent.futures
import ftplib
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import time

STATE = ".sunmintz-deploy-state.json"
LEGACY_STATE = ".ftp-deploy-sync-state.json"
BATCH_SIZE = 32


def safe_path(name):
    if (not isinstance(name, str) or not name or name.startswith("/")
            or "\\" in name or any(ord(c) < 32 for c in name)
            or any(part in ("", ".", "..") for part in name.split("/"))
            or name in (STATE, LEGACY_STATE) or name.endswith(".deploy-tmp")):
        raise ValueError(f"Invalid deployment path: {name!r}")
    return name


def inventory(root):
    files = {}
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise ValueError(f"Symlinks are not supported: {path}")
        if not path.is_file() or path.name == ".DS_Store":
            continue
        name = safe_path(path.relative_to(root).as_posix())
        files[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    if "index.html" not in files:
        raise ValueError("Export is missing index.html; refusing deployment")
    return files


def read_json(ftp, name):
    data = io.BytesIO()
    try:
        ftp.retrbinary(f"RETR {name}", data.write)
    except ftplib.error_perm as error:
        if not str(error).startswith("550"):
            raise
        # Distinguish an absent file from denied read access.
        if name in [PurePosixPath(p).name for p in ftp.nlst()]:
            raise
        return None
    return json.loads(data.getvalue())


def load_state(ftp):
    state = read_json(ftp, STATE)
    if state is not None:
        if state["version"] != 1:
            raise ValueError("Unsupported deployment manifest version")
        files = state["files"]
    else:
        legacy = read_json(ftp, LEGACY_STATE)
        if legacy is None:
            print("No manifest found: initial full upload required.", flush=True)
            files = {}
        else:
            if legacy["version"] != "1.0.0":
                raise ValueError("Unsupported legacy deployment manifest")
            files = {item["name"]: item["hash"] for item in legacy["data"]
                     if item["type"] == "file"}
            print(f"Reusing {len(files)} hashes from the previous uploader.", flush=True)
    for name, digest in files.items():
        safe_path(name)
        if digest is not None and (
                not isinstance(digest, str) or len(digest) != 64
                or any(c not in "0123456789abcdef" for c in digest)):
            raise ValueError(f"Invalid hash for {name}")
    return files


def save_state(ftp, files):
    data = json.dumps({"version": 1, "files": files}).encode()
    ftp.storbinary(f"STOR {STATE}.deploy-tmp", io.BytesIO(data))
    ftp.rename(f"{STATE}.deploy-tmp", STATE)


def upload_group(connect, root, names):
    """One connection per worker, reconnecting on a failed transfer."""
    ftp = None
    done, errors = [], []
    directories = set()
    try:
        for name in names:
            for attempt in range(3):
                try:
                    if ftp is None:
                        ftp = connect()
                        directories.clear()
                    parent = PurePosixPath(name).parent
                    for directory in reversed([parent, *parent.parents]):
                        directory = str(directory)
                        if directory == "." or directory in directories:
                            continue
                        try:
                            ftp.mkd(directory)
                        except ftplib.error_perm:
                            # Existing directory is fine; permissions errors are not.
                            base = ftp.pwd()
                            ftp.cwd(directory)
                            ftp.cwd(base)
                        directories.add(directory)
                    with (root / name).open("rb") as source:
                        ftp.storbinary(f"STOR {name}.deploy-tmp", source, 256 * 1024)
                    ftp.rename(f"{name}.deploy-tmp", name)
                    done.append(name)
                    break
                except (OSError, EOFError, ftplib.Error) as error:
                    if ftp:
                        ftp.close()
                    ftp = None
                    if attempt == 2:
                        errors.append(f"{name}: {type(error).__name__}")
                    else:
                        time.sleep(2 ** attempt)
    finally:
        if ftp:
            ftp.close()
    return done, errors


def deploy(root, connect, fresh=False, workers=4):
    current = inventory(root)
    control = connect()
    try:
        previous = load_state(control)
        changed = [name for name in current if fresh or current[name] != previous.get(name)]
        removed = [name for name in previous if name not in current
                   and not name.startswith("_next/static/")]
        size = sum((root / name).stat().st_size for name in changed)
        summary = (f"{len(changed)} changed/new, {len(current) - len(changed)} unchanged, "
                   f"{len(removed)} removed; upload {size / 1024 / 1024:.2f} MiB")
        print(summary, flush=True)
        if os.environ.get("GITHUB_STEP_SUMMARY"):
            with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as output:
                output.write(f"### Deployment\n\n{summary}\n")
        # Invalidate pending hashes BEFORE mutating the server. Even a killed run
        # followed by a revert must not trust the old hash for a modified file.
        state = dict(previous)
        for name in changed:
            state[name] = None
        save_state(control, state)
    finally:
        control.close()

    # Upload dependencies before HTML; keep old hashed chunks for open browsers.
    phases = [[n for n in changed if not n.endswith(".html")],
              [n for n in changed if n.endswith(".html")]]
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        for names in phases:
            for start in range(0, len(names), BATCH_SIZE):
                batch = names[start:start + BATCH_SIZE]
                jobs = [pool.submit(upload_group, connect, root, batch[i::workers])
                        for i in range(min(workers, len(batch)))]
                errors = []
                for job in jobs:
                    done, failures = job.result()
                    state.update({name: current[name] for name in done})
                    errors.extend(failures)
                control = connect()
                try:
                    save_state(control, state)
                finally:
                    control.close()
                print(f"Checkpoint: {sum(v is not None for v in state.values())} confirmed files",
                      flush=True)
                if errors:
                    raise RuntimeError("Uploads failed (rerun to resume): " + "; ".join(errors))

    control = connect()
    try:
        # Delete only files in our manifest, after every upload has succeeded.
        for name in removed:
            try:
                control.delete(name)
            except ftplib.error_perm as error:
                if not str(error).startswith("550"):
                    raise
                if PurePosixPath(name).name in [
                    PurePosixPath(p).name for p in control.nlst(str(PurePosixPath(name).parent))
                ]:
                    raise
            del state[name]
        save_state(control, state)
    finally:
        control.close()


def connect():
    ftp = ftplib.FTP(timeout=60)
    try:
        ftp.connect(os.environ["FTP_SERVER"], int(os.environ.get("FTP_PORT", "21")))
        ftp.login(os.environ["FTP_USERNAME"], os.environ["FTP_PASSWORD"])
        ftp.cwd(os.environ["FTP_SERVER_DIR"])
        return ftp
    except BaseException:
        ftp.close()
        raise


if __name__ == "__main__":
    deploy(Path("out"), connect, fresh=os.environ.get("FRESH") == "true")
