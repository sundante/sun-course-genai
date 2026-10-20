import contextlib
import ftplib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("deploy", Path(__file__).parents[1] / "deploy.py")
deploy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(deploy)


class FakeFTP:
    def __init__(self, files):
        self.files = files
        self.uploads = []
        self.fail = None

    def retrbinary(self, command, callback):
        name = command[5:]
        if name not in self.files:
            raise ftplib.error_perm("550 No such file")
        callback(self.files[name])

    def storbinary(self, command, source, *_):
        name = command[5:]
        if name == self.fail:
            raise OSError("Connection lost")
        self.files[name] = source.read()
        self.uploads.append(name)

    def rename(self, old, new):
        self.files[new] = self.files.pop(old)

    def delete(self, name):
        self.files.pop(name, None)

    def nlst(self, directory="."):
        return list(self.files)

    def mkd(self, directory):
        pass

    def close(self):
        pass


class DeployTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "index.html").write_text("home")
        (self.root / "index.txt").write_text("navigation payload")
        self.ftp = FakeFTP({})

    def run_deploy(self, **kwargs):
        with contextlib.redirect_stdout(io.StringIO()), patch.object(deploy.time, "sleep"):
            deploy.deploy(self.root, lambda: self.ftp, **kwargs)

    def content_uploads(self):
        return [p for p in self.ftp.uploads if p != deploy.STATE + ".deploy-tmp"]

    def test_initial_and_identical_deploy(self):
        self.run_deploy()
        self.assertEqual(self.ftp.files["index.txt"], b"navigation payload")
        self.ftp.uploads.clear()
        self.run_deploy()
        self.assertEqual(self.content_uploads(), [])

    def test_only_changed_files_and_deletions(self):
        self.run_deploy()
        self.ftp.uploads.clear()
        (self.root / "index.html").write_text("changed")
        (self.root / "index.txt").unlink()
        self.run_deploy()
        self.assertEqual(self.content_uploads(), ["index.html.deploy-tmp"])
        self.assertNotIn("index.txt", self.ftp.files)

    def test_legacy_manifest_avoids_reupload(self):
        files = deploy.inventory(self.root)
        self.ftp.files[deploy.LEGACY_STATE] = json.dumps({
            "version": "1.0.0",
            "data": [{"type": "file", "name": k, "hash": v} for k, v in files.items()]
        }).encode()
        self.run_deploy()
        self.assertEqual(self.content_uploads(), [])

    def test_failed_upload_resumes_without_repeating_successes(self):
        self.ftp.fail = "index.html.deploy-tmp"
        with self.assertRaises(RuntimeError):
            self.run_deploy()
        self.assertIsNone(json.loads(self.ftp.files[deploy.STATE])["files"]["index.html"])
        self.ftp.fail = None
        self.ftp.uploads.clear()
        self.run_deploy()
        self.assertEqual(self.content_uploads(), ["index.html.deploy-tmp"])

    def test_reverted_file_after_interruption_is_not_skipped(self):
        self.run_deploy()
        state = json.loads(self.ftp.files[deploy.STATE])
        state["files"]["index.html"] = None
        self.ftp.files[deploy.STATE] = json.dumps(state).encode()
        self.ftp.files["index.html"] = b"partially deployed newer version"
        self.run_deploy()
        self.assertEqual(self.ftp.files["index.html"], b"home")

    def test_failure_keeps_old_html_and_defers_deletions(self):
        self.run_deploy()
        (self.root / "index.txt").unlink()
        (self.root / "index.html").write_text("new home")
        self.ftp.fail = "index.html.deploy-tmp"
        with self.assertRaises(RuntimeError):
            self.run_deploy()
        self.assertEqual(self.ftp.files["index.html"], b"home")
        self.assertIn("index.txt", self.ftp.files)

    def test_transient_connection_failure_retries(self):
        attempts = 0

        def flaky_connect():
            nonlocal attempts
            attempts += 1
            if attempts == 1:
                raise OSError("Temporary connection failure")
            return self.ftp

        with patch.object(deploy.time, "sleep"):
            done, failures = deploy.upload_group(flaky_connect, self.root, ["index.html"])
        self.assertEqual(done, ["index.html"])
        self.assertEqual(failures, [])
        self.assertEqual(attempts, 2)

    def test_fresh_preserves_unmanaged_files_and_old_chunks(self):
        self.ftp.files[".htaccess"] = b"host config"
        self.ftp.files["_next/static/old.js"] = b"old chunk"
        self.ftp.files[deploy.STATE] = json.dumps({
            "version": 1, "files": {
                "_next/static/old.js": hashlib.sha256(b"old chunk").hexdigest()
            }
        }).encode()
        self.run_deploy(fresh=True)
        self.assertEqual(self.ftp.files[".htaccess"], b"host config")
        self.assertEqual(self.ftp.files["_next/static/old.js"], b"old chunk")

    def test_invalid_manifest_fails_before_writes(self):
        self.ftp.files[deploy.STATE] = b'{"version":1,"files":{"../outside":null}}'
        with self.assertRaises(ValueError):
            self.run_deploy()
        self.assertEqual(self.ftp.uploads, [])

    def test_empty_export_fails_before_connecting(self):
        (self.root / "index.html").unlink()
        with self.assertRaises(ValueError):
            self.run_deploy()
        self.assertEqual(self.ftp.uploads, [])


if __name__ == "__main__":
    unittest.main()
