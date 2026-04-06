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
from urllib.parse import urlparse

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


def _yaml_value(raw_line: str) -> str | None:
    value = raw_line.split(":", 1)[1].strip().strip("\"'")
    return value or None


def read_model_settings(path: Path) -> dict[str, str | None]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return {"default": None, "base_url": None}

    in_model = False
    model_indent = 0
    settings = {"default": None, "base_url": None}

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
            settings["default"] = _yaml_value(stripped)
        if in_model and stripped.startswith("base_url:"):
            settings["base_url"] = _yaml_value(stripped)

    return settings


def model_vendor_name(model_name: str | None) -> str | None:
    if not model_name or "/" not in model_name:
        return None
    vendor = model_name.split("/", 1)[0].strip().lower()
    return vendor or None


def endpoint_kind(base_url: str | None) -> str:
    if not base_url:
        return "default provider"
    if is_local_router_base_url(base_url):
        return "local router"
    return "custom endpoint"


def is_local_router_base_url(base_url: str | None) -> bool:
    if not base_url:
        return False
    parsed = urlparse(base_url)
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    return parsed.hostname in {"127.0.0.1", "localhost"} and port == 8788


def endpoint_display_name(base_url: str | None, model_name: str | None) -> str:
    if is_local_router_base_url(base_url):
        return "ghostship-router"
    if base_url:
        parsed = urlparse(base_url)
        host = parsed.hostname or ""
        if host == "openrouter.ai":
            return "openrouter"
        if host:
            return host
    return model_vendor_name(model_name) or "default"


def detect_auth_source(base_url: str | None, env_payload: dict[str, str]) -> str | None:
    if is_local_router_base_url(base_url):
        for key in ("OPENAI_API_KEY", "GHOSTSHIP_ROUTER_API_KEY", "API_SERVER_KEY"):
            if env_payload.get(key):
                return key
        return None
    if base_url and urlparse(base_url).hostname == "openrouter.ai" and env_payload.get("OPENROUTER_API_KEY"):
        return "OPENROUTER_API_KEY"
    return None


def router_http_headers(env_payload: dict[str, str]) -> dict[str, str]:
    token = (
        env_payload.get("OPENAI_API_KEY")
        or env_payload.get("GHOSTSHIP_ROUTER_API_KEY")
        or env_payload.get("API_SERVER_KEY")
    )
    return {"Authorization": f"Bearer {token}"} if token else {}


def fetch_router_enrichment(base_url: str, env_payload: dict[str, str]) -> dict[str, Any] | None:
    router_base = base_url.rstrip("/")
    if router_base.endswith("/v1"):
        router_base = router_base[:-3]
    headers = router_http_headers(env_payload)

    try:
        with httpx.Client(timeout=1.5, follow_redirects=True) as client:
            ready_response = client.get(f"{router_base}/readyz")
            ready_response.raise_for_status()
            ready_payload = ready_response.json()

            providers_response = client.get(f"{router_base}/debug/providers")
            providers_response.raise_for_status()
            providers_payload = providers_response.json()

            aliases: list[dict[str, Any]] = []
            models_response = client.get(f"{router_base}/v1/models", headers=headers)
            if models_response.status_code == 200:
                for item in models_response.json().get("data", []):
                    metadata = item.get("metadata") or {}
                    aliases.append(
                        {
                            "name": item.get("id"),
                            "description": metadata.get("description"),
                            "candidate_count": metadata.get("candidate_count", 0),
                            "candidates": metadata.get("candidates", []),
                        }
                    )
            else:
                for alias_name in ("auxiliary", "coding", "agentic", "vision", "tts"):
                    route_response = client.get(f"{router_base}/debug/routes/{alias_name}")
                    if route_response.status_code != 200:
                        continue
                    route_payload = route_response.json()
                    candidates = route_payload.get("candidates", [])
                    aliases.append(
                        {
                            "name": alias_name,
                            "description": None,
                            "candidate_count": len(candidates),
                            "candidates": candidates,
                        }
                    )

            return {
                "reachable": True,
                "ready": bool(ready_payload.get("ok")),
                "detail": ready_payload.get("detail"),
                "providers": providers_payload if isinstance(providers_payload, list) else [],
                "aliases": aliases,
            }
    except (httpx.HTTPError, ValueError):
        return None


def current_environment_payload() -> dict[str, Any]:
    profiles_root = Path(MANAGED_HERMES_HOME) / "profiles"
    root_env_path = Path(MANAGED_HERMES_HOME) / ".env"
    root_config_path = Path(MANAGED_HERMES_HOME) / "config.yaml"
    runtime_env = {
        key: value
        for key in (
            "OPENAI_API_KEY",
            "GHOSTSHIP_ROUTER_API_KEY",
            "API_SERVER_KEY",
            "OPENROUTER_API_KEY",
            "OPENROUTER_BASE_URL",
            "OPENROUTER_HTTP_REFERER",
            "OPENROUTER_TITLE",
        )
        if (value := os.environ.get(key))
    }
    root_env = parse_env_file(root_env_path) or runtime_env
    root_settings = read_model_settings(root_config_path)
    root_model = root_settings["default"]
    root_base_url = root_settings["base_url"]
    endpoints: dict[str, dict[str, Any]] = {}
    endpoint_models: dict[str, dict[str, dict[str, Any]]] = {}

    def register_model(endpoint_key: str, model_name: str | None, *, scope: str, profile_name: str | None = None) -> None:
        if not model_name:
            return
        model_map = endpoint_models.setdefault(endpoint_key, {})
        entry = model_map.setdefault(
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

    def register_endpoint(
        *,
        base_url: str | None,
        model_name: str | None,
        env_payload: dict[str, str],
        scope: str,
        profile_name: str | None = None,
    ) -> None:
        key = base_url or f"default::{model_vendor_name(model_name) or 'default'}"
        auth_source = detect_auth_source(base_url, env_payload)
        entry = endpoints.setdefault(
            key,
            {
                "name": endpoint_display_name(base_url, model_name),
                "kind": endpoint_kind(base_url),
                "configured": bool(base_url or model_name),
                "base_url": base_url,
                "auth_source": auth_source,
                "models": [],
                "profiles": [],
                "router": None,
            },
        )
        if auth_source and not entry.get("auth_source"):
            entry["auth_source"] = auth_source
        if profile_name and profile_name not in entry["profiles"]:
            entry["profiles"].append(profile_name)
        register_model(key, model_name, scope=scope, profile_name=profile_name)

    profiles = []
    register_endpoint(base_url=root_base_url, model_name=root_model, env_payload=root_env | runtime_env, scope="root")

    for name in MANAGED_PROFILES:
        profile_root = profiles_root / name
        profile_env = parse_env_file(profile_root / ".env")
        profile_settings = read_model_settings(profile_root / "config.yaml")
        profile_model = profile_settings["default"] or root_model
        profile_base_url = profile_settings["base_url"] or root_base_url
        register_endpoint(
            base_url=profile_base_url,
            model_name=profile_model,
            env_payload=profile_env | root_env | runtime_env,
            scope="profile",
            profile_name=name,
        )

        profiles.append(
            {
                "name": name,
                "path": str(profile_root),
                "service": f"ghostship-hermes-profile-{name}.service",
                "is_default": name == DEFAULT_PROFILE,
                "model": profile_model,
                "base_url": profile_base_url,
                "endpoint_name": endpoint_display_name(profile_base_url, profile_model),
                "model_vendor": model_vendor_name(profile_model),
                "has_env": safe_path_exists(profile_root / ".env"),
                "has_config": safe_path_exists(profile_root / "config.yaml"),
            }
        )

    providers: list[dict[str, Any]] = []
    for key, entry in endpoints.items():
        entry["models"] = sorted(endpoint_models.get(key, {}).values(), key=lambda item: item["name"])
        if is_local_router_base_url(entry["base_url"]):
            entry["router"] = fetch_router_enrichment(entry["base_url"], root_env | runtime_env)
        providers.append(entry)

    default_profile_model = next((profile["model"] for profile in profiles if profile["is_default"]), None)

    return {
        "host": socket.gethostname(),
        "dashboard_bind": f"{DASHBOARD_HOST}:{DASHBOARD_PORT}",
        "terminal_cwd": TERMINAL_CWD,
        "home": HOME_DIR,
        "managed_hermes_home": MANAGED_HERMES_HOME,
        "default_profile": DEFAULT_PROFILE,
        "root_base_url": root_base_url,
        "root_model": root_model,
        "default_profile_model": default_profile_model,
        "model": root_model,
        "providers": sorted(providers, key=lambda item: item["name"]),
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
