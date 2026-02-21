from __future__ import annotations

import socket
import subprocess
import sys
import time
from pathlib import Path

import webview


REPO_ROOT = Path(__file__).resolve().parent
PYTHON_EXE = REPO_ROOT / ".venv" / "Scripts" / "python.exe"
WEB_LAUNCHER = REPO_ROOT / "openmanus_web_launcher.py"
HOST = "127.0.0.1"
PORT = 8765
URL = f"http://{HOST}:{PORT}"


def wait_for_port(host: str, port: int, timeout_sec: int = 20) -> bool:
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(1)
            if sock.connect_ex((host, port)) == 0:
                return True
        time.sleep(0.2)
    return False


def main() -> int:
    if not PYTHON_EXE.exists():
        print(f"Python do venv nao encontrado: {PYTHON_EXE}")
        return 1
    if not WEB_LAUNCHER.exists():
        print(f"Launcher web nao encontrado: {WEB_LAUNCHER}")
        return 1

    process = subprocess.Popen(
        [str(PYTHON_EXE), str(WEB_LAUNCHER), "--host", HOST, "--port", str(PORT)],
        cwd=str(REPO_ROOT),
    )
    try:
        if not wait_for_port(HOST, PORT):
            print("Nao foi possivel subir o launcher web.")
            process.terminate()
            return 1

        webview.create_window(
            "OpenManus Desktop",
            URL,
            width=1280,
            height=860,
            min_size=(980, 680),
        )
        webview.start()
        return 0
    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()


if __name__ == "__main__":
    raise SystemExit(main())
