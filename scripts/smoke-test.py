"""Check current exported routes locally before deployment, then over HTTP."""

from pathlib import Path
import sys
import time
from urllib.error import URLError
from urllib.request import urlopen

TARGETS = {
    "": "index.html",
    "learn/pretraining/index/": "learn/pretraining/index/index.html",
    "learn/pretraining/index/index.txt": "learn/pretraining/index/index.txt",
    "labs/gpt/index.html": "labs/gpt/index.html",
    "robots.txt": "robots.txt",
}


def main():
    for route, filename in TARGETS.items():
        if not (Path("out") / filename).is_file():
            raise RuntimeError(f"Smoke-test target no longer exists in export: {filename}")
    if "--local" in sys.argv:
        print("All smoke-test targets exist in out/.")
        return
    for route in TARGETS:
        for attempt in range(3):
            try:
                with urlopen(f"https://learngenai.sunmintz.com/{route}", timeout=20) as response:
                    if response.status != 200:
                        raise RuntimeError(f"Unexpected status: {response.status}")
                    print(f"200 /{route}", flush=True)
                break
            except (URLError, OSError, RuntimeError):
                if attempt == 2:
                    raise
                time.sleep(3)


if __name__ == "__main__":
    main()
