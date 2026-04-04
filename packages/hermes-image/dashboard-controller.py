#!/usr/bin/env python3
import http.client
import json
import mimetypes
import os
import select
import shlex
import shutil
import signal
import socket
import subprocess
import threading
import time
import uuid
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit


STATE_DIR = Path(os.environ.get("GHOSTSHIP_DASHBOARD_STATE_DIR", "/home/hermes/.local/state/ghostship-hermes/dashboard"))
STATE_FILE = STATE_DIR / "state.json"
LOG_DIR = STATE_DIR / "logs"
TTYD_HOST = os.environ.get("GHOSTSHIP_TTYD_HOST", "127.0.0.1")
TTYD_PORT_BASE = int(os.environ.get("GHOSTSHIP_TTYD_PORT_BASE", "7682"))
DASHBOARD_HOST = os.environ.get("GHOSTSHIP_DASHBOARD_HOST", "0.0.0.0")
DASHBOARD_PORT = int(os.environ.get("GHOSTSHIP_DASHBOARD_PORT", "7683"))
TERMINAL_CWD = os.environ.get("GHOSTSHIP_TERMINAL_CWD", "/home/hermes")
HOME_DIR = os.environ.get("HOME", "/home/hermes")
MANAGED_HERMES_HOME = os.environ.get("HERMES_HOME", "/home/hermes/.hermes")
TTYD_TITLE = os.environ.get("GHOSTSHIP_TTYD_TITLE", "ghostship-hermes")
DASHBOARD_ROOT = Path(os.environ.get("GHOSTSHIP_DASHBOARD_ROOT", "/srv/dashboard"))
BASH_PATH = os.environ.get("GHOSTSHIP_BASH") or shutil.which("bash") or "/bin/sh"

STATE_LOCK = threading.Lock()


def ensure_state_dir() -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)


def wait_for_port(host: str, port: int, timeout: float = 10.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(0.2)
            try:
                sock.connect((host, port))
                return True
            except OSError:
                time.sleep(0.15)
    return False


def process_is_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def load_state() -> dict:
    ensure_state_dir()
    if not STATE_FILE.exists():
        return {"next_index": 1, "active_terminal_id": None, "sessions": []}
    try:
        payload = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"next_index": 1, "active_terminal_id": None, "sessions": []}

    payload.setdefault("next_index", 1)
    payload.setdefault("active_terminal_id", None)
    payload.setdefault("sessions", [])
    return payload


def save_state(state: dict) -> None:
    STATE_FILE.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")


def prune_dead_sessions(state: dict) -> dict:
    alive_sessions = [session for session in state["sessions"] if process_is_alive(session["pid"])]
    state["sessions"] = alive_sessions
    session_ids = {session["id"] for session in alive_sessions}
    if state["active_terminal_id"] not in session_ids:
        state["active_terminal_id"] = alive_sessions[-1]["id"] if alive_sessions else None
    return state


def terminal_payload(state: dict) -> dict:
    profiles_root = Path(HOME_DIR) / ".hermes" / "profiles"
    profiles = [
        {"name": "default", "path": str(Path(HOME_DIR) / ".hermes")},
    ]
    if profiles_root.is_dir():
        for entry in sorted(profiles_root.iterdir()):
            if entry.is_dir():
                profiles.append({"name": entry.name, "path": str(entry)})
    return {
        "terminal_cwd": TERMINAL_CWD,
        "home": HOME_DIR,
        "managed_hermes_home": MANAGED_HERMES_HOME,
        "active_terminal_id": state["active_terminal_id"],
        "profiles": profiles,
        "sessions": [
            {
                "id": session["id"],
                "label": session["label"],
                "pid": session["pid"],
                "port": session["port"],
                "terminal_url": session["terminal_url"],
                "cwd": session["cwd"],
            }
            for session in state["sessions"]
        ],
    }


def available_port(state: dict) -> int:
    used_ports = {session["port"] for session in state["sessions"]}
    port = TTYD_PORT_BASE
    while port in used_ports:
        port += 1
    return port


def ttyd_command(session: dict) -> list[str]:
    shell_command = f"cd {shlex.quote(TERMINAL_CWD)} && exec {shlex.quote(BASH_PATH)} -l"
    return [
        "ttyd",
        "--writable",
        "-i",
        TTYD_HOST,
        "-p",
        str(session["port"]),
        "--base-path",
        session["terminal_url"].rstrip("/"),
        "-t",
        f"titleFixed={TTYD_TITLE} · {session['label']}",
        BASH_PATH,
        "-lc",
        shell_command,
    ]


def open_terminal() -> dict:
    with STATE_LOCK:
        state = prune_dead_sessions(load_state())
        label = f"Terminal {state['next_index']}"
        session_id = uuid.uuid4().hex[:10]
        session = {
            "id": session_id,
            "label": label,
            "port": available_port(state),
            "cwd": TERMINAL_CWD,
            "terminal_url": f"/terminals/{session_id}/",
            "started_at": int(time.time()),
        }
        log_path = LOG_DIR / f"{session_id}.log"
        with log_path.open("ab") as log_handle:
            process = subprocess.Popen(
                ttyd_command(session),
                cwd=TERMINAL_CWD,
                env=os.environ.copy(),
                stdout=log_handle,
                stderr=log_handle,
                start_new_session=True,
            )
        session["pid"] = process.pid

        if not wait_for_port(TTYD_HOST, session["port"]):
            terminate_session(session)
            raise RuntimeError(f"ttyd did not start on {TTYD_HOST}:{session['port']}")

        state["next_index"] += 1
        state["sessions"].append(session)
        state["active_terminal_id"] = session_id
        save_state(state)
        return terminal_payload(state)


def terminate_session(session: dict) -> None:
    pid = session.get("pid")
    if not pid or not process_is_alive(pid):
        return
    try:
        os.killpg(pid, signal.SIGTERM)
    except OSError:
        return
    deadline = time.monotonic() + 5.0
    while time.monotonic() < deadline and process_is_alive(pid):
        time.sleep(0.1)
    if process_is_alive(pid):
        try:
            os.killpg(pid, signal.SIGKILL)
        except OSError:
            pass


def close_terminal(session_id: str) -> dict:
    with STATE_LOCK:
        state = prune_dead_sessions(load_state())
        session = next((entry for entry in state["sessions"] if entry["id"] == session_id), None)
        if session is None:
            return terminal_payload(state)

        terminate_session(session)
        state["sessions"] = [entry for entry in state["sessions"] if entry["id"] != session_id]
        if state["active_terminal_id"] == session_id:
            state["active_terminal_id"] = state["sessions"][-1]["id"] if state["sessions"] else None
        save_state(state)
        return terminal_payload(state)


def current_status() -> dict:
    with STATE_LOCK:
        state = prune_dead_sessions(load_state())
        save_state(state)
        return terminal_payload(state)


def get_terminal_session(request_path: str) -> dict | None:
    request_path = urlsplit(request_path).path
    if not request_path.startswith("/terminals/"):
        return None
    parts = request_path.split("/")
    if len(parts) < 3 or not parts[2]:
        return None
    terminal_id = parts[2]
    state = prune_dead_sessions(load_state())
    for session in state["sessions"]:
        if session["id"] == terminal_id:
            return session
    return None


def hop_by_hop_header(name: str) -> bool:
    return name.lower() in {
        "connection",
        "keep-alive",
        "proxy-authenticate",
        "proxy-authorization",
        "te",
        "trailers",
        "transfer-encoding",
        "upgrade",
    }


class RequestHandler(BaseHTTPRequestHandler):
    server_version = "ghostship-hermes-dashboard/2.0"

    def _write_json(self, payload: dict, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload, indent=2) + "\n"
        encoded = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def _serve_static(self) -> None:
        request_path = urlsplit(self.path).path
        relative = "index.html" if request_path in {"", "/"} else request_path.lstrip("/")
        target = (DASHBOARD_ROOT / relative).resolve()
        try:
            target.relative_to(DASHBOARD_ROOT.resolve())
        except ValueError:
            self._write_json({"error": "not found"}, HTTPStatus.NOT_FOUND)
            return
        if not target.is_file():
            self._write_json({"error": "not found"}, HTTPStatus.NOT_FOUND)
            return

        content = target.read_bytes()
        content_type = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def _proxy_terminal_http(self) -> None:
        session = get_terminal_session(self.path)
        if session is None:
            self._write_json({"error": "terminal not found"}, HTTPStatus.NOT_FOUND)
            return

        parsed = urlsplit(self.path)
        connection = http.client.HTTPConnection(TTYD_HOST, session["port"], timeout=30)
        headers = {
            key: value
            for key, value in self.headers.items()
            if not hop_by_hop_header(key)
        }
        headers["Host"] = f"{TTYD_HOST}:{session['port']}"
        body = None
        if "Content-Length" in self.headers:
            body = self.rfile.read(int(self.headers["Content-Length"]))
        connection.request(self.command, parsed.path + (f"?{parsed.query}" if parsed.query else ""), body=body, headers=headers)
        response = connection.getresponse()
        payload = response.read()

        self.send_response(response.status, response.reason)
        for key, value in response.getheaders():
            if hop_by_hop_header(key):
                continue
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(payload)
        connection.close()

    def _proxy_terminal_websocket(self) -> None:
        session = get_terminal_session(self.path)
        if session is None:
            self._write_json({"error": "terminal not found"}, HTTPStatus.NOT_FOUND)
            return

        parsed = urlsplit(self.path)
        upstream = socket.create_connection((TTYD_HOST, session["port"]))
        upstream.setblocking(False)
        request_lines = [f"{self.command} {parsed.path + (f'?{parsed.query}' if parsed.query else '')} HTTP/1.1"]
        for key, value in self.headers.items():
            if key.lower() == "host":
                value = f"{TTYD_HOST}:{session['port']}"
            request_lines.append(f"{key}: {value}")
        upstream.sendall(("\r\n".join(request_lines) + "\r\n\r\n").encode("utf-8"))

        response_head = bytearray()
        while b"\r\n\r\n" not in response_head:
            chunk = upstream.recv(65536)
            if not chunk:
                upstream.close()
                self.close_connection = True
                return
            response_head.extend(chunk)

        head, remainder = response_head.split(b"\r\n\r\n", 1)
        self.connection.sendall(head + b"\r\n\r\n" + remainder)
        self.connection.setblocking(False)

        sockets = [self.connection, upstream]
        try:
            while True:
                readable, _, exceptional = select.select(sockets, [], sockets, 60)
                if exceptional:
                    break
                if not readable:
                    continue
                for current in readable:
                    peer = upstream if current is self.connection else self.connection
                    try:
                        data = current.recv(65536)
                    except OSError:
                        data = b""
                    if not data:
                        return
                    peer.sendall(data)
        finally:
            upstream.close()
            self.close_connection = True

    def do_GET(self) -> None:
        if self.headers.get("Upgrade", "").lower() == "websocket" and self.path.startswith("/terminals/"):
            self._proxy_terminal_websocket()
            return
        if self.path == "/api/status":
            self._write_json(current_status())
            return
        if self.path == "/healthz":
            self._write_json({"ok": True})
            return
        if self.path.startswith("/terminals/"):
            self._proxy_terminal_http()
            return
        self._serve_static()

    def do_POST(self) -> None:
        if self.path == "/api/terminal/open":
            try:
                self._write_json(open_terminal())
            except RuntimeError as exc:
                self._write_json({"error": str(exc)}, HTTPStatus.BAD_GATEWAY)
            return

        if self.path.startswith("/api/terminals/") and self.path.endswith("/close"):
            session_id = self.path.removeprefix("/api/terminals/").removesuffix("/close").strip("/")
            if not session_id:
                self._write_json({"error": "terminal id required"}, HTTPStatus.BAD_REQUEST)
                return
            try:
                self._write_json(close_terminal(session_id))
            except RuntimeError as exc:
                self._write_json({"error": str(exc)}, HTTPStatus.BAD_GATEWAY)
            return

        if self.path.startswith("/terminals/"):
            self._proxy_terminal_http()
            return
        self._write_json({"error": "not found"}, HTTPStatus.NOT_FOUND)

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        return


def main() -> None:
    ensure_state_dir()
    current_status()
    server = ThreadingHTTPServer((DASHBOARD_HOST, DASHBOARD_PORT), RequestHandler)
    server.serve_forever()


if __name__ == "__main__":
    main()
