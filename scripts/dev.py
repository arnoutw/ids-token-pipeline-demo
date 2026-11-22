#!/usr/bin/env python3
"""Rebuild on changes and serve the demo locally without dependencies."""

from __future__ import annotations

import subprocess
import threading
import time
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WATCH = [ROOT / "tokens", ROOT / "site", ROOT / "scripts" / "build.py"]
OUTPUT = ROOT / "dist" / "site"


def stamp() -> tuple:
    files = []
    for target in WATCH:
        if target.is_file():
            files.append(target)
        elif target.exists():
            files.extend(path for path in target.rglob("*") if path.is_file())
    return tuple(sorted((str(path), path.stat().st_mtime_ns, path.stat().st_size) for path in files))


def build() -> None:
    subprocess.run(["python3", str(ROOT / "scripts" / "build.py")], check=True, cwd=ROOT)


def watch() -> None:
    previous = stamp()
    while True:
        time.sleep(0.7)
        current = stamp()
        if current != previous:
            try:
                build()
                print("Rebuilt — refresh the browser.")
            except subprocess.CalledProcessError:
                print("Build failed; fix the token file and save again.")
            previous = current


def main() -> None:
    build()
    handler = lambda *args, **kwargs: SimpleHTTPRequestHandler(*args, directory=str(OUTPUT), **kwargs)
    server = ThreadingHTTPServer(("127.0.0.1", 8000), handler)
    threading.Thread(target=watch, daemon=True).start()
    url = "http://127.0.0.1:8000"
    print(f"Serving {url} — press Ctrl+C to stop.")
    threading.Timer(0.4, lambda: webbrowser.open(url)).start()
    server.serve_forever()


if __name__ == "__main__":
    main()
