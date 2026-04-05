import asyncio
import json
import logging
import os
import shlex
import shutil
import signal
import socket
import subprocess
import time
import uuid
from pathlib import Path
from typing import Any

import httpx
import uvicorn
import websockets
from fastapi import FastAPI, HTTPException, Request, Response, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("hermes_dashboard")

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
MANAGED_PROFILES = [item.strip() for item in os.environ.get("GHOSTSHIP_HERMES_PROFILES", "operations,coder").split(",") if item.strip()]
DEFAULT_PROFILE = os.environ.get("GHOSTSHIP_HERMES_DEFAULT_PROFILE", MANAGED_PROFILES[0] if MANAGED_PROFILES else "default")
BASH_PATH = os.environ.get("GHOSTSHIP_BASH") or shutil.which("bash") or "/bin/sh"
DASHBOARD_ROOT = Path(__file__).parent / "static"

app = FastAPI(title="ghostship-hermes-dashboard")
state_lock = asyncio.Lock()


def ensure_state_dir() -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)


def port_is_open(host: str, port: int, timeout: float = 0.15) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(timeout)
        try:
            sock.connect((host, port))
            return True
        except OSError:
            return False


def process_is_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def load_state() -> dict[str, Any]:
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


def save_state(state: dict[str, Any]) -> None:
    STATE_FILE.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")


def child_pids(pid: int) -> list[int]:
    try:
        children = Path(f"/proc/{pid}/task/{pid}/children").read_text(encoding="utf-8").strip()
    except OSError:
        return []
    if not children:
        return []
    return [int(item) for item in children.split() if item.isdigit()]


def deepest_descendant(pid: int) -> int:
    current = pid
    while True:
        children = child_pids(current)
        if not children:
            return current
        current = children[-1]


def proc_name(pid: int) -> str:
    for candidate in (f"/proc/{pid}/comm", f"/proc/{pid}/cmdline"):
        try:
            raw = Path(candidate).read_bytes()
        except OSError:
            continue
        if not raw:
            continue
        if candidate.endswith("/cmdline"):
            name = raw.replace(b"\x00", b" ").decode("utf-8", errors="ignore").strip()
            if name:
                return name
        else:
            name = raw.decode("utf-8", errors="ignore").strip()
            if name:
                return name
    return ""


def proc_cwd(pid: int) -> str:
    try:
        cwd = os.readlink(f"/proc/{pid}/cwd")
    except OSError:
        return ""
    if cwd.startswith(HOME_DIR):
        suffix = cwd[len(HOME_DIR):].lstrip("/")
        return f"/home/hermes/{suffix}" if suffix else "/home/hermes"
    return cwd


def session_label(session: dict[str, Any]) -> str:
    ttyd_pid = session["pid"]
    shell_pid = child_pids(ttyd_pid)
    if not shell_pid:
        return session["cwd"] or session["label"]
    active_pid = deepest_descendant(shell_pid[-1])
    active_name = proc_name(active_pid)
    if active_name:
        try:
            command = shlex.split(active_name)[0] if active_name.strip() else ""
        except ValueError:
            command = active_name.split(" ", 1)[0]
        command_name = Path(command).name
        if command_name and command_name not in {"bash", "sh"}:
            return command_name
    cwd = proc_cwd(active_pid)
    return cwd or session["cwd"] or session["label"]


def prune_dead_sessions(state: dict[str, Any]) -> dict[str, Any]:
    alive_sessions = [session for session in state["sessions"] if process_is_alive(session["pid"])]
    state["sessions"] = alive_sessions
    session_ids = {session["id"] for session in alive_sessions}
    if state["active_terminal_id"] not in session_ids:
        state["active_terminal_id"] = alive_sessions[-1]["id"] if alive_sessions else None
    return state


def terminal_payload(state: dict[str, Any]) -> dict[str, Any]:
    profiles = []
    profiles_root = Path(MANAGED_HERMES_HOME) / "profiles"
    for name in MANAGED_PROFILES:
        profiles.append(
            {
                "name": name,
                "path": str(profiles_root / name),
                "service": f"ghostship-hermes-profile-{name}.service",
                "is_default": name == DEFAULT_PROFILE,
            }
        )
    return {
        "terminal_cwd": TERMINAL_CWD,
        "home": HOME_DIR,
        "managed_hermes_home": MANAGED_HERMES_HOME,
        "default_profile": DEFAULT_PROFILE,
        "active_terminal_id": state["active_terminal_id"],
        "profiles": profiles,
        "sessions": [
            {
                "id": session["id"],
                "label": session_label(session),
                "pid": session["pid"],
                "port": session["port"],
                "terminal_url": session["terminal_url"],
                "cwd": session["cwd"],
                "ready": port_is_open(TTYD_HOST, session["port"]),
            }
            for session in state["sessions"]
        ],
    }


def available_port(state: dict[str, Any]) -> int:
    used_ports = {session["port"] for session in state["sessions"]}
    port = TTYD_PORT_BASE
    while port in used_ports:
        port += 1
    return port


def ttyd_command(session: dict[str, Any]) -> list[str]:
    shell_command = f"cd {shlex.quote(TERMINAL_CWD)} && exec {shlex.quote(BASH_PATH)} -l"
    return [
        "ttyd",
        "--writable",
        "-i",
        TTYD_HOST,
        "-p",
        str(session["port"]),
        "-t",
        "disableLeaveAlert=true",
        "-t",
        "disableResizeOverlay=true",
        "-t",
        "rendererType=webgl",
        "-t",
        "fontFamily=IBM Plex Mono, monospace",
        "-t",
        "theme={\"background\":\"#050505\",\"foreground\":\"#20c20e\",\"cursor\":\"#f0a84d\",\"selectionBackground\":\"rgba(32,194,14,0.28)\",\"black\":\"#050505\",\"red\":\"#ff3366\",\"green\":\"#20c20e\",\"yellow\":\"#f0a84d\",\"blue\":\"#33ccff\",\"magenta\":\"#c18cff\",\"cyan\":\"#63d8e6\",\"white\":\"#d6dcea\",\"brightBlack\":\"#333333\",\"brightRed\":\"#ff6699\",\"brightGreen\":\"#4dff4d\",\"brightYellow\":\"#ffcc66\",\"brightBlue\":\"#66d9ff\",\"brightMagenta\":\"#d2abff\",\"brightCyan\":\"#96ecf5\",\"brightWhite\":\"#ffffff\"}",
        "--base-path",
        session["terminal_url"].rstrip("/"),
        BASH_PATH,
        "-lc",
        shell_command,
    ]


async def open_terminal_logic() -> dict[str, Any]:
    async with state_lock:
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

        state["next_index"] += 1
        state["sessions"].append(session)
        state["active_terminal_id"] = session_id
        save_state(state)
        return terminal_payload(state)


def terminate_session(session: dict[str, Any], timeout: float = 0.75) -> None:
    pid = session.get("pid")
    if not pid or not process_is_alive(pid):
        return
    try:
        os.killpg(pid, signal.SIGTERM)
    except OSError:
        return
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline and process_is_alive(pid):
        time.sleep(0.05)
    if process_is_alive(pid):
        try:
            os.killpg(pid, signal.SIGKILL)
        except OSError:
            pass


async def close_terminal_logic(session_id: str) -> dict[str, Any]:
    async with state_lock:
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


async def current_status_logic() -> dict[str, Any]:
    async with state_lock:
        state = prune_dead_sessions(load_state())
        save_state(state)
        return terminal_payload(state)


def get_terminal_session(terminal_id: str) -> dict[str, Any] | None:
    state = prune_dead_sessions(load_state())
    for session in state["sessions"]:
        if session["id"] == terminal_id:
            return session
    return None


@app.get("/api/status")
async def get_status():
    return await current_status_logic()


@app.post("/api/terminal/open")
async def open_terminal():
    try:
        return await open_terminal_logic()
    except Exception as e:
        logger.exception("Failed to open terminal")
        raise HTTPException(status_code=502, detail=str(e))


@app.post("/api/terminals/{session_id}/close")
async def close_terminal(session_id: str):
    try:
        return await close_terminal_logic(session_id)
    except Exception as e:
        logger.exception("Failed to close terminal")
        raise HTTPException(status_code=502, detail=str(e))


@app.get("/healthz")
def healthz():
    return {"ok": True}


async def _proxy_http(request: Request, session_id: str, path: str):
    session = get_terminal_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Terminal not found")
    
    url = f"http://{TTYD_HOST}:{session['port']}/terminals/{session_id}/{path}"
    query = request.url.query
    if query:
        url += f"?{query}"
        
    client = httpx.AsyncClient()
    headers = dict(request.headers)
    headers.pop("host", None)
    headers.pop("connection", None)
    headers.pop("keep-alive", None)
    
    try:
        body = await request.body()
        req = client.build_request(
            method=request.method,
            url=url,
            headers=headers,
            content=body
        )
        resp = await client.send(req, stream=True)
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="Terminal is starting")
    
    async def stream_response():
        async for chunk in resp.aiter_raw():
            yield chunk
            
    response_headers = dict(resp.headers)
    response_headers.pop("content-encoding", None)
    response_headers.pop("transfer-encoding", None)
    response_headers.pop("content-length", None)
    
    return StreamingResponse(
        stream_response(),
        status_code=resp.status_code,
        headers=response_headers
    )


@app.api_route("/terminals/{session_id}/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD", "PATCH", "TRACE"])
async def proxy_terminal_http(request: Request, session_id: str, path: str):
    return await _proxy_http(request, session_id, path)


@app.websocket("/terminals/{session_id}/{path:path}")
async def proxy_terminal_websocket(websocket: WebSocket, session_id: str, path: str):
    session = get_terminal_session(session_id)
    if not session:
        await websocket.close(code=1008)
        return
        
    await websocket.accept()
    query = websocket.url.query
    target_url = f"ws://{TTYD_HOST}:{session['port']}/terminals/{session_id}/{path}"
    if query:
        target_url += f"?{query}"
        
    try:
        async with websockets.connect(target_url, subprotocols=websocket.headers.get("sec-websocket-protocol", "").split(", ")) as upstream_ws:
            async def forward_to_upstream():
                try:
                    while True:
                        data = await websocket.receive()
                        if "text" in data:
                            await upstream_ws.send(data["text"])
                        elif "bytes" in data:
                            await upstream_ws.send(data["bytes"])
                except WebSocketDisconnect:
                    pass
                except Exception as e:
                    logger.error(f"Error forwarding to upstream: {e}")

            async def forward_to_client():
                try:
                    while True:
                        message = await upstream_ws.recv()
                        if isinstance(message, str):
                            await websocket.send_text(message)
                        else:
                            await websocket.send_bytes(message)
                except websockets.exceptions.ConnectionClosed:
                    pass
                except Exception as e:
                    logger.error(f"Error forwarding to client: {e}")

            await asyncio.gather(forward_to_upstream(), forward_to_client())
    except Exception as e:
        logger.error(f"WebSocket proxy failed: {e}")
        try:
            await websocket.close(code=1011)
        except Exception:
            pass


@app.get("/")
def serve_index():
    index_file = DASHBOARD_ROOT / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return HTMLResponse("<html><body>Frontend not found</body></html>", status_code=404)


app.mount("/", StaticFiles(directory=str(DASHBOARD_ROOT)), name="static")


def main() -> None:
    ensure_state_dir()
    uvicorn.run(app, host=DASHBOARD_HOST, port=DASHBOARD_PORT)


if __name__ == "__main__":
    main()
