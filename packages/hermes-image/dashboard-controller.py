#!/usr/bin/env python3
import json
import os
import shlex
import signal
import socket
import subprocess
import time
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


STATE_DIR = Path(os.environ.get("GHOSTSHIP_DASHBOARD_STATE_DIR", "/data/.ghostship/dashboard"))
TTYD_PORT = int(os.environ.get("GHOSTSHIP_TTYD_PORT", "7682"))
TTYD_HOST = os.environ.get("GHOSTSHIP_TTYD_HOST", "127.0.0.1")
TTYD_BASE_PATH = os.environ.get("GHOSTSHIP_TTYD_BASE_PATH", "/terminal")
DASHBOARD_PORT = int(os.environ.get("GHOSTSHIP_DASHBOARD_PORT", "7683"))
WORKSPACE = os.environ.get("MESSAGING_CWD", "/workspace")
TTYD_TITLE = os.environ.get("GHOSTSHIP_TTYD_TITLE", "ghostship-hermes")

PID_FILE = STATE_DIR / "ttyd.pid"
STATUS_FILE = STATE_DIR / "status.json"
LOG_FILE = STATE_DIR / "ttyd.log"


def ensure_state_dir() -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)


def wait_for_port(host: str, port: int, timeout: float = 10.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(0.2)
            try:
                sock.connect((host, port))
                return True
            except OSError:
                time.sleep(0.2)
    return False


def read_pid() -> int | None:
    if not PID_FILE.exists():
        return None
    try:
        return int(PID_FILE.read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        return None


def process_is_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def clear_terminal_state() -> None:
    for path in (PID_FILE, STATUS_FILE):
        try:
            path.unlink()
        except FileNotFoundError:
            pass


def terminal_status() -> dict:
    ensure_state_dir()
    pid = read_pid()
    if pid is None or not process_is_alive(pid):
        clear_terminal_state()
        return {
            "running": False,
            "pid": None,
            "terminal_url": TTYD_BASE_PATH,
            "workspace": WORKSPACE,
        }

    return {
        "running": True,
        "pid": pid,
        "terminal_url": TTYD_BASE_PATH,
        "workspace": WORKSPACE,
    }


def write_status(status: dict) -> None:
    STATUS_FILE.write_text(json.dumps(status, indent=2) + "\n", encoding="utf-8")


def ttyd_command() -> list[str]:
    shell_command = f"cd {shlex.quote(WORKSPACE)} && exec bash -l"
    return [
        "ttyd",
        "--writable",
        "-i",
        TTYD_HOST,
        "-p",
        str(TTYD_PORT),
        "--base-path",
        TTYD_BASE_PATH,
        "-t",
        f"titleFixed={TTYD_TITLE}",
        "bash",
        "-lc",
        shell_command,
    ]


def open_terminal() -> dict:
    status = terminal_status()
    if status["running"]:
        return status

    ensure_state_dir()
    with LOG_FILE.open("ab") as log_handle:
        process = subprocess.Popen(
            ttyd_command(),
            cwd=WORKSPACE,
            env=os.environ.copy(),
            stdout=log_handle,
            stderr=log_handle,
            start_new_session=True,
        )

    PID_FILE.write_text(f"{process.pid}\n", encoding="utf-8")

    if not wait_for_port(TTYD_HOST, TTYD_PORT):
        close_terminal()
        raise RuntimeError(f"ttyd did not start on {TTYD_HOST}:{TTYD_PORT}")

    status = terminal_status()
    write_status(status)
    return status


def close_terminal() -> dict:
    pid = read_pid()
    if pid is not None and process_is_alive(pid):
        try:
            os.killpg(pid, signal.SIGTERM)
        except OSError:
            pass
        deadline = time.monotonic() + 5.0
        while time.monotonic() < deadline and process_is_alive(pid):
            time.sleep(0.1)
        if process_is_alive(pid):
            try:
                os.killpg(pid, signal.SIGKILL)
            except OSError:
                pass

    clear_terminal_state()
    status = terminal_status()
    write_status(status)
    return status


class RequestHandler(BaseHTTPRequestHandler):
    server_version = "ghostship-hermes-dashboard/1.0"

    def _write_json(self, payload: dict, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload, indent=2) + "\n"
        encoded = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def do_GET(self) -> None:
        if self.path == "/api/status":
            self._write_json(terminal_status())
            return
        if self.path == "/healthz":
            self._write_json({"ok": True})
            return
        self._write_json({"error": "not found"}, HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:
        if self.path == "/api/terminal/open":
            try:
                self._write_json(open_terminal())
            except RuntimeError as exc:
                self._write_json({"error": str(exc)}, HTTPStatus.BAD_GATEWAY)
            return

        if self.path == "/api/terminal/close":
            self._write_json(close_terminal())
            return

        self._write_json({"error": "not found"}, HTTPStatus.NOT_FOUND)

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        return


def main() -> None:
    ensure_state_dir()
    write_status(terminal_status())
    server = ThreadingHTTPServer(("127.0.0.1", DASHBOARD_PORT), RequestHandler)
    server.serve_forever()


if __name__ == "__main__":
    main()
