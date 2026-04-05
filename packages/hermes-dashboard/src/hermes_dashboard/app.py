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
from starlette.background import BackgroundTask
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


def safe_path_exists(path: Path) -> bool:
    try:
        return path.exists()
    except OSError:
        return False


def parse_env_file(path: Path) -> dict[str, str]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return {}

    payload: dict[str, str] = {}
    for raw_line in lines:
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        payload[key.strip()] = value.strip()
    return payload


def read_model_default(path: Path) -> str | None:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return None

    in_model = False
    model_indent = 0

    for raw_line in lines:
        line = raw_line.split("#", 1)[0].rstrip()
        if not line.strip():
            continue

        indent = len(raw_line) - len(raw_line.lstrip(" "))
        stripped = line.strip()

        if stripped == "model:":
            in_model = True
            model_indent = indent
            continue

        if in_model and indent <= model_indent:
            in_model = False

        if in_model and stripped.startswith("default:"):
            value = stripped.split(":", 1)[1].strip().strip("\"'")
            return value or None

    return None


def model_vendor_name(model_name: str | None) -> str | None:
    if not model_name or "/" not in model_name:
        return None
    vendor = model_name.split("/", 1)[0].strip().lower()
    return vendor or None


def has_openrouter_config(env_payload: dict[str, str]) -> bool:
    return any(env_payload.get(key) for key in ("OPENROUTER_API_KEY", "OPENROUTER_BASE_URL", "OPENROUTER_HTTP_REFERER", "OPENROUTER_TITLE"))


def current_environment_payload() -> dict[str, Any]:
    profiles_root = Path(MANAGED_HERMES_HOME) / "profiles"
    root_env_path = Path(MANAGED_HERMES_HOME) / ".env"
    root_config_path = Path(MANAGED_HERMES_HOME) / "config.yaml"
    runtime_env = {
        key: value
        for key in (
            "OPENROUTER_API_KEY",
            "OPENROUTER_BASE_URL",
            "OPENROUTER_HTTP_REFERER",
            "OPENROUTER_TITLE",
            "OPENROUTER_TEST_MODEL",
        )
        if (value := os.environ.get(key))
    }
    root_env = parse_env_file(root_env_path) or runtime_env
    root_model = read_model_default(root_config_path) or os.environ.get("OPENROUTER_TEST_MODEL")
    openrouter_env = root_env | runtime_env
    has_openrouter = has_openrouter_config(openrouter_env)
    model_entries: dict[str, dict[str, Any]] = {}

    def register_model(model_name: str | None, *, scope: str, profile_name: str | None = None) -> None:
        if not model_name:
            return
        entry = model_entries.setdefault(
            model_name,
            {
                "name": model_name,
                "vendor": model_vendor_name(model_name),
                "scopes": [],
                "profiles": [],
            },
        )
        if scope not in entry["scopes"]:
            entry["scopes"].append(scope)
        if profile_name and profile_name not in entry["profiles"]:
            entry["profiles"].append(profile_name)

    register_model(root_model, scope="runtime")

    profiles = []
    for name in MANAGED_PROFILES:
        profile_root = profiles_root / name
        profile_env = parse_env_file(profile_root / ".env")
        profile_model = read_model_default(profile_root / "config.yaml") or root_model
        has_openrouter = has_openrouter or has_openrouter_config(profile_env)
        register_model(profile_model, scope="profile", profile_name=name)

        profiles.append(
            {
                "name": name,
                "path": str(profile_root),
                "service": f"ghostship-hermes-profile-{name}.service",
                "is_default": name == DEFAULT_PROFILE,
                "model": profile_model,
                "model_vendor": model_vendor_name(profile_model),
                "has_env": safe_path_exists(profile_root / ".env"),
                "has_config": safe_path_exists(profile_root / "config.yaml"),
            }
        )

    providers = []
    if has_openrouter:
        providers.append(
            {
                "name": "openrouter",
                "configured": bool(openrouter_env.get("OPENROUTER_API_KEY")),
                "base_url": openrouter_env.get("OPENROUTER_BASE_URL") or "https://openrouter.ai/api/v1",
                "has_api_key": bool(openrouter_env.get("OPENROUTER_API_KEY")),
                "has_referer": bool(openrouter_env.get("OPENROUTER_HTTP_REFERER")),
                "title": openrouter_env.get("OPENROUTER_TITLE") or None,
                "models": sorted(model_entries.values(), key=lambda item: item["name"]),
            }
        )

    return {
        "host": socket.gethostname(),
        "dashboard_bind": f"{DASHBOARD_HOST}:{DASHBOARD_PORT}",
        "terminal_cwd": TERMINAL_CWD,
        "home": HOME_DIR,
        "managed_hermes_home": MANAGED_HERMES_HOME,
        "default_profile": DEFAULT_PROFILE,
        "model": root_model,
        "providers": providers,
        "profiles": profiles,
    }


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
        "environment": current_environment_payload(),
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
    while port in used_ports or port_is_open(TTYD_HOST, port):
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

        # ttyd fails fast on bind/path issues; surface that immediately instead
        # of saving a dead session that points at an unrelated stale listener.
        await asyncio.sleep(0.15)
        if process.poll() is not None:
            raise RuntimeError(f"ttyd exited during startup with code {process.returncode}")

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
        async for chunk in resp.aiter_bytes():
            yield chunk

    async def close_upstream() -> None:
        await resp.aclose()
        await client.aclose()

    response_headers = dict(resp.headers)
    response_headers.pop("content-encoding", None)
    response_headers.pop("transfer-encoding", None)
    response_headers.pop("content-length", None)

    return StreamingResponse(
        stream_response(),
        status_code=resp.status_code,
        headers=response_headers,
        background=BackgroundTask(close_upstream),
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

    query = websocket.url.query
    target_url = f"ws://{TTYD_HOST}:{session['port']}/terminals/{session_id}/{path}"
    if query:
        target_url += f"?{query}"

    requested_subprotocols = [
        value.strip()
        for value in websocket.headers.get("sec-websocket-protocol", "").split(",")
        if value.strip()
    ]

    try:
        async with websockets.connect(
            target_url,
            subprotocols=requested_subprotocols or None,
        ) as upstream_ws:
            await websocket.accept(subprotocol=upstream_ws.subprotocol)

            async def forward_to_upstream() -> None:
                while True:
                    data = await websocket.receive()
                    if data.get("type") == "websocket.disconnect":
                        break
                    if "text" in data:
                        await upstream_ws.send(data["text"])
                    elif "bytes" in data:
                        await upstream_ws.send(data["bytes"])

            async def forward_to_client() -> None:
                async for message in upstream_ws:
                    if isinstance(message, str):
                        await websocket.send_text(message)
                    else:
                        await websocket.send_bytes(message)

            upstream_task = asyncio.create_task(forward_to_upstream())
            client_task = asyncio.create_task(forward_to_client())
            done, pending = await asyncio.wait(
                {upstream_task, client_task},
                return_when=asyncio.FIRST_COMPLETED,
            )

            for task in pending:
                task.cancel()
            if pending:
                await asyncio.gather(*pending, return_exceptions=True)
            for task in done:
                exc = task.exception()
                if exc and not isinstance(exc, WebSocketDisconnect):
                    raise exc
    except WebSocketDisconnect:
        pass
    except websockets.exceptions.ConnectionClosed:
        pass
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
