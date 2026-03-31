#!/usr/bin/env python3
"""Launch the Solidify browser wizard for a questionnaire session."""

from __future__ import annotations

import argparse
import json
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Launch the Solidify GUI wizard.")
    parser.add_argument("--session-dir", required=True, help="Session directory containing questionnaire.json")
    return parser.parse_args()


def is_server_alive(port: int) -> bool:
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=1):
            return True
    except (urllib.error.URLError, TimeoutError, OSError):
        return False


def choose_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def wait_for_server(port: int, timeout_s: float = 5.0) -> bool:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        if is_server_alive(port):
            return True
        time.sleep(0.1)
    return False


def main() -> int:
    args = parse_args()
    session_dir = Path(args.session_dir).expanduser().resolve()
    session_dir.mkdir(parents=True, exist_ok=True)

    if not (session_dir / "questionnaire.json").exists():
        print(f"Missing questionnaire.json in {session_dir}", file=sys.stderr)
        return 1

    server_info_path = session_dir / "server.json"
    if server_info_path.exists():
        try:
            server_info = json.loads(server_info_path.read_text())
            port = int(server_info["port"])
            if is_server_alive(port):
                url = f"http://127.0.0.1:{port}/"
                webbrowser.open(url)
                print(url)
                return 0
        except (json.JSONDecodeError, KeyError, ValueError):
            pass

    port = choose_free_port()
    server_script = Path(__file__).with_name("wizard_server.py")
    command = [sys.executable, str(server_script), "--session-dir", str(session_dir), "--port", str(port)]
    env = os.environ.copy()
    subprocess.Popen(
        command,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL,
        start_new_session=True,
        env=env,
    )

    if not wait_for_server(port):
        print(f"Wizard server failed to start on port {port}", file=sys.stderr)
        return 1

    url = f"http://127.0.0.1:{port}/"
    webbrowser.open(url)
    print(url)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
