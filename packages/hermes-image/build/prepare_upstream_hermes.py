from __future__ import annotations

import sys
from pathlib import Path


CONSOLE_HELPER = r'''from __future__ import annotations

import asyncio
import json
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
import websockets
from fastapi import HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from starlette.background import BackgroundTask

STATE_DIR = Path(
    os.environ.get(
        "GHOSTSHIP_DASHBOARD_STATE_DIR",
        "/home/hermes/.local/state/ghostship-hermes/dashboard",
    )
)
STATE_FILE = STATE_DIR / "console-state.json"
LOG_DIR = STATE_DIR / "logs"
TTYD_HOST = os.environ.get("GHOSTSHIP_TTYD_HOST", "127.0.0.1")
TTYD_PORT_BASE = int(os.environ.get("GHOSTSHIP_TTYD_PORT_BASE", "7682"))
TERMINAL_CWD = os.environ.get("GHOSTSHIP_TERMINAL_CWD", "/workspace")
HOME_DIR = os.environ.get("HOME", "/home/hermes")
MANAGED_HERMES_HOME = os.environ.get("HERMES_HOME", "/home/hermes/.hermes")
BASH_PATH = shutil.which("bash") or "/bin/sh"
TTYD_THEME = json.dumps(
    {
        "background": "#041C1C",
        "foreground": "#FFE6CB",
        "cursor": "#FFE6CB",
        "cursorAccent": "#041C1C",
        "selectionBackground": "#0C3838",
        "black": "#041C1C",
        "red": "#FB7185",
        "green": "#4ADE80",
        "yellow": "#FFBD38",
        "blue": "#67E8F9",
        "magenta": "#F9A8D4",
        "cyan": "#5EEAD4",
        "white": "#FFE6CB",
        "brightBlack": "#0A2E2E",
        "brightRed": "#FCA5A5",
        "brightGreen": "#86EFAC",
        "brightYellow": "#FCD34D",
        "brightBlue": "#A5F3FC",
        "brightMagenta": "#FBCFE8",
        "brightCyan": "#99F6E4",
        "brightWhite": "#FFF5E6",
    },
    separators=(",", ":"),
)

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
    ensure_state_dir()
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
        "fontFamily=Courier Prime, monospace",
        "-t",
        "fontSize=14",
        "-t",
        f"theme={TTYD_THEME}",
        "--base-path",
        session["terminal_url"].rstrip("/"),
        BASH_PATH,
        "-lc",
        shell_command,
    ]


def _serialize_session(session: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": session["id"],
        "label": session_label(session),
        "pid": session["pid"],
        "port": session["port"],
        "terminal_url": session["terminal_url"],
        "cwd": session["cwd"],
        "ready": port_is_open(TTYD_HOST, session["port"]),
    }


def console_payload(state: dict[str, Any]) -> dict[str, Any]:
    sessions = [_serialize_session(session) for session in state["sessions"]]
    active_session_id = state.get("active_terminal_id")
    active_session = next((session for session in sessions if session["id"] == active_session_id), None)
    if active_session is None and sessions:
        active_session = sessions[-1]
        active_session_id = active_session["id"]
    return {
        "terminal_cwd": TERMINAL_CWD,
        "home": HOME_DIR,
        "managed_hermes_home": MANAGED_HERMES_HOME,
        "active_session_id": active_session_id,
        "session": active_session,
        "sessions": sessions,
    }


async def get_console_status() -> dict[str, Any]:
    async with state_lock:
        state = prune_dead_sessions(load_state())
        save_state(state)
        return console_payload(state)


async def open_console_session() -> dict[str, Any]:
    async with state_lock:
        state = prune_dead_sessions(load_state())
        if state["sessions"]:
            if not state.get("active_terminal_id"):
                state["active_terminal_id"] = state["sessions"][-1]["id"]
            save_state(state)
            return console_payload(state)

        label = f"Console {state['next_index']}"
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

        await asyncio.sleep(0.25)
        if process.poll() is not None:
            raise RuntimeError(f"ttyd exited during startup with code {process.returncode}")

        session["pid"] = process.pid
        state["next_index"] += 1
        state["sessions"] = [session]
        state["active_terminal_id"] = session_id
        save_state(state)
        return console_payload(state)


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


async def close_console_session(session_id: str) -> dict[str, Any]:
    async with state_lock:
        state = prune_dead_sessions(load_state())
        session = next((entry for entry in state["sessions"] if entry["id"] == session_id), None)
        if session is None:
            save_state(state)
            return console_payload(state)
        terminate_session(session)
        state["sessions"] = [entry for entry in state["sessions"] if entry["id"] != session_id]
        if state.get("active_terminal_id") == session_id:
            state["active_terminal_id"] = state["sessions"][-1]["id"] if state["sessions"] else None
        save_state(state)
        return console_payload(state)


def get_console_session(session_id: str) -> dict[str, Any] | None:
    state = prune_dead_sessions(load_state())
    for session in state["sessions"]:
        if session["id"] == session_id:
            return session
    return None


async def proxy_terminal_http(request: Request, session_id: str, path: str):
    session = get_console_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Console session not found")

    url = f"http://{TTYD_HOST}:{session['port']}/terminals/{session_id}/{path}"
    if request.url.query:
        url += f"?{request.url.query}"

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
            content=body,
        )
        resp = await client.send(req, stream=True)
    except httpx.RequestError as exc:
        await client.aclose()
        raise HTTPException(status_code=503, detail="Console is starting") from exc

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


async def proxy_terminal_websocket(websocket: WebSocket, session_id: str, path: str) -> None:
    session = get_console_session(session_id)
    if not session:
        await websocket.close(code=1008)
        return

    target_url = f"ws://{TTYD_HOST}:{session['port']}/terminals/{session_id}/{path}"
    if websocket.url.query:
        target_url += f"?{websocket.url.query}"

    requested_subprotocols = [
        value.strip()
        for value in websocket.headers.get("sec-websocket-protocol", "").split(",")
        if value.strip()
    ]

    try:
        async with websockets.connect(target_url, subprotocols=requested_subprotocols or None) as upstream_ws:
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
            done, pending = await asyncio.wait({upstream_task, client_task}, return_when=asyncio.FIRST_COMPLETED)
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
    except Exception:
        try:
            await websocket.close(code=1011)
        except Exception:
            pass
'''

CONSOLE_PAGE = r'''import { TerminalSquare } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function ConsolePage() {
  return (
    <div className="grid gap-6 lg:grid-cols-[320px_minmax(0,1fr)]">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <TerminalSquare className="h-4 w-4" />
            Console
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2 text-sm text-muted-foreground">
            <p>Workspace: <span className="font-mono-ui text-foreground">/workspace</span></p>
            <p>Path: <span className="font-mono-ui text-foreground">/terminal/</span></p>
            <p>The terminal stays embedded in the Hermes web UI and is backed by the local ttyd sidecar.</p>
          </div>
        </CardContent>
      </Card>

      <Card className="overflow-hidden">
        <CardHeader>
          <CardTitle className="text-base">Terminal</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <iframe
            title="Hermes Console"
            src="/terminal/"
            className="h-[70vh] w-full border-0 bg-background"
            sandbox="allow-same-origin allow-scripts allow-forms"
          />
        </CardContent>
      </Card>
    </div>
  );
}
'''

def replace_once(text: str, old: str, new: str, *, path: Path) -> str:
    if old not in text:
        raise RuntimeError(f"missing patch marker in {path}: {old[:80]!r}")
    return text.replace(old, new, 1)


def main() -> None:
    root = Path(sys.argv[1]).resolve()

    gateway_run = root / "gateway" / "run.py"
    gateway_text = gateway_run.read_text(encoding="utf-8")
    turn_route_marker_old = """    def _resolve_turn_agent_config(self, user_message: str, model: str, runtime_kwargs: dict) -> dict:\n        from agent.smart_model_routing import resolve_turn_route\n        from hermes_cli.models import resolve_fast_mode_overrides\n\n        primary = {\n            \"model\": model,\n            \"api_key\": runtime_kwargs.get(\"api_key\"),\n            \"base_url\": runtime_kwargs.get(\"base_url\"),\n            \"provider\": runtime_kwargs.get(\"provider\"),\n            \"api_mode\": runtime_kwargs.get(\"api_mode\"),\n            \"command\": runtime_kwargs.get(\"command\"),\n            \"args\": list(runtime_kwargs.get(\"args\") or []),\n            \"credential_pool\": runtime_kwargs.get(\"credential_pool\"),\n        }\n        route = resolve_turn_route(user_message, getattr(self, \"_smart_model_routing\", {}), primary)\n"""
    turn_route_replacement_old = """    @staticmethod\n    def _ghostship_discord_forced_channel(source) -> str | None:\n        if source is None:\n            return None\n        platform = getattr(source, \"platform\", None)\n        platform_value = getattr(platform, \"value\", platform)\n        if platform_value != \"discord\":\n            return None\n        if getattr(source, \"chat_type\", None) == \"dm\":\n            return None\n        codex_channel = os.getenv(\"GHOSTSHIP_CODEX_CHANNEL\", \"\").strip()\n        if not codex_channel:\n            return None\n        chat_id = getattr(source, \"chat_id\", None)\n        parent_chat_id = getattr(source, \"chat_id_alt\", None)\n        if chat_id == codex_channel or parent_chat_id == codex_channel:\n            return \"codex\"\n        return None\n\n    @staticmethod\n    def _ghostship_force_discord_codex_channel_route(runtime_kwargs: dict) -> dict:\n        forced_runtime = dict(runtime_kwargs)\n        forced_runtime[\"base_url\"] = None\n        forced_runtime[\"provider\"] = \"openai-codex\"\n        forced_runtime[\"api_mode\"] = \"codex_responses\"\n        forced_runtime[\"command\"] = None\n        forced_runtime[\"args\"] = []\n        forced_runtime[\"credential_pool\"] = None\n        return forced_runtime\n\n    def _resolve_turn_agent_config(self, user_message: str, model: str, runtime_kwargs: dict, source=None) -> dict:\n        from agent.smart_model_routing import resolve_turn_route\n        from hermes_cli.models import resolve_fast_mode_overrides\n\n        forced_channel = self._ghostship_discord_forced_channel(source)\n        if forced_channel == \"codex\":\n            primary = {\n                \"model\": \"gpt-5.5\",\n                \"base_url\": None,\n                \"provider\": \"openai-codex\",\n                \"api_mode\": \"codex_responses\",\n                \"command\": None,\n                \"args\": [],\n                \"credential_pool\": None,\n            }\n            route = resolve_turn_route(user_message, getattr(self, \"_smart_model_routing\", {}), primary)\n            route[\"model\"] = \"gpt-5.5\"\n            route[\"runtime\"] = self._ghostship_force_discord_codex_channel_route(route.get(\"runtime\", {}))\n            route[\"label\"] = \"ghostship discord codex channel pin\"\n            route[\"request_overrides\"] = None\n            route[\"signature\"] = (\n                route[\"model\"],\n                route[\"runtime\"].get(\"provider\"),\n                route[\"runtime\"].get(\"base_url\"),\n                route[\"runtime\"].get(\"api_mode\"),\n                route[\"runtime\"].get(\"command\"),\n                tuple(route[\"runtime\"].get(\"args\") or ()),\n            )\n        else:\n            primary = {\n                \"model\": model,\n                \"api_key\": runtime_kwargs.get(\"api_key\"),\n                \"base_url\": runtime_kwargs.get(\"base_url\"),\n                \"provider\": runtime_kwargs.get(\"provider\"),\n                \"api_mode\": runtime_kwargs.get(\"api_mode\"),\n                \"command\": runtime_kwargs.get(\"command\"),\n                \"args\": list(runtime_kwargs.get(\"args\") or []),\n                \"credential_pool\": runtime_kwargs.get(\"credential_pool\"),\n            }\n            route = resolve_turn_route(user_message, getattr(self, \"_smart_model_routing\", {}), primary)\n"""
    turn_route_marker_new = """    def _resolve_turn_agent_config(self, user_message: str, model: str, runtime_kwargs: dict) -> dict:\n        \"\"\"Build the effective model/runtime config for a single turn.\n\n        Always uses the session's primary model/provider.  If `/fast` is\n        enabled and the model supports Priority Processing / Anthropic fast\n        mode, attach `request_overrides` so the API call is marked\n        accordingly.\n        \"\"\"\n        from hermes_cli.models import resolve_fast_mode_overrides\n\n        runtime = {\n            \"api_key\": runtime_kwargs.get(\"api_key\"),\n            \"base_url\": runtime_kwargs.get(\"base_url\"),\n            \"provider\": runtime_kwargs.get(\"provider\"),\n            \"api_mode\": runtime_kwargs.get(\"api_mode\"),\n            \"command\": runtime_kwargs.get(\"command\"),\n            \"args\": list(runtime_kwargs.get(\"args\") or []),\n            \"credential_pool\": runtime_kwargs.get(\"credential_pool\"),\n        }\n        route = {\n            \"model\": model,\n            \"runtime\": runtime,\n            \"signature\": (\n                model,\n                runtime[\"provider\"],\n                runtime[\"base_url\"],\n                runtime[\"api_mode\"],\n                runtime[\"command\"],\n                tuple(runtime[\"args\"]),\n            ),\n        }\n"""
    turn_route_replacement_new = """    @staticmethod\n    def _ghostship_discord_forced_channel(source) -> str | None:\n        if source is None:\n            return None\n        platform = getattr(source, \"platform\", None)\n        platform_value = getattr(platform, \"value\", platform)\n        if platform_value != \"discord\":\n            return None\n        if getattr(source, \"chat_type\", None) == \"dm\":\n            return None\n        codex_channel = os.getenv(\"GHOSTSHIP_CODEX_CHANNEL\", \"\").strip()\n        if not codex_channel:\n            return None\n        chat_id = getattr(source, \"chat_id\", None)\n        parent_chat_id = getattr(source, \"chat_id_alt\", None)\n        if chat_id == codex_channel or parent_chat_id == codex_channel:\n            return \"codex\"\n        return None\n\n    @staticmethod\n    def _ghostship_force_discord_codex_channel_route(runtime_kwargs: dict) -> dict:\n        forced_runtime = dict(runtime_kwargs)\n        forced_runtime[\"base_url\"] = None\n        forced_runtime[\"provider\"] = \"openai-codex\"\n        forced_runtime[\"api_mode\"] = \"codex_responses\"\n        forced_runtime[\"command\"] = None\n        forced_runtime[\"args\"] = []\n        forced_runtime[\"credential_pool\"] = None\n        return forced_runtime\n\n    def _resolve_turn_agent_config(self, user_message: str, model: str, runtime_kwargs: dict, source=None) -> dict:\n        \"\"\"Build the effective model/runtime config for a single turn.\n\n        Always uses the session's primary model/provider.  If `/fast` is\n        enabled and the model supports Priority Processing / Anthropic fast\n        mode, attach `request_overrides` so the API call is marked\n        accordingly.\n        \"\"\"\n        from hermes_cli.models import resolve_fast_mode_overrides\n\n        forced_channel = self._ghostship_discord_forced_channel(source)\n        if forced_channel == \"codex\":\n            runtime = self._ghostship_force_discord_codex_channel_route(runtime_kwargs)\n            route = {\n                \"model\": \"gpt-5.5\",\n                \"runtime\": runtime,\n                \"signature\": (\n                    \"gpt-5.5\",\n                    runtime[\"provider\"],\n                    runtime[\"base_url\"],\n                    runtime[\"api_mode\"],\n                    runtime[\"command\"],\n                    tuple(runtime[\"args\"]),\n                ),\n            }\n            route[\"label\"] = \"ghostship discord codex channel pin\"\n            route[\"request_overrides\"] = None\n            return route\n\n        runtime = {\n            \"api_key\": runtime_kwargs.get(\"api_key\"),\n            \"base_url\": runtime_kwargs.get(\"base_url\"),\n            \"provider\": runtime_kwargs.get(\"provider\"),\n            \"api_mode\": runtime_kwargs.get(\"api_mode\"),\n            \"command\": runtime_kwargs.get(\"command\"),\n            \"args\": list(runtime_kwargs.get(\"args\") or []),\n            \"credential_pool\": runtime_kwargs.get(\"credential_pool\"),\n        }\n        route = {\n            \"model\": model,\n            \"runtime\": runtime,\n            \"signature\": (\n                model,\n                runtime[\"provider\"],\n                runtime[\"base_url\"],\n                runtime[\"api_mode\"],\n                runtime[\"command\"],\n                tuple(runtime[\"args\"]),\n            ),\n        }\n"""
    if turn_route_marker_old in gateway_text:
        gateway_text = replace_once(gateway_text, turn_route_marker_old, turn_route_replacement_old, path=gateway_run)
    else:
        gateway_text = replace_once(gateway_text, turn_route_marker_new, turn_route_replacement_new, path=gateway_run)
    for old, new in (
        (
            "            turn_route = self._resolve_turn_agent_config(prompt, model, runtime_kwargs)\n",
            "            turn_route = self._resolve_turn_agent_config(prompt, model, runtime_kwargs, source)\n",
        ),
        (
            "            turn_route = self._resolve_turn_agent_config(question, model, runtime_kwargs)\n",
            "            turn_route = self._resolve_turn_agent_config(question, model, runtime_kwargs, source)\n",
        ),
        (
            "            turn_route = self._resolve_turn_agent_config(message, model, runtime_kwargs)\n",
            "            turn_route = self._resolve_turn_agent_config(message, model, runtime_kwargs, source)\n",
        ),
        (
            """        # No args: show interactive picker (Telegram/Discord) or text list\n        if not model_input and not explicit_provider:\n""",
            """        forced_channel = self._ghostship_discord_forced_channel(source)\n        if forced_channel == \"codex\":\n            self._session_model_overrides.pop(session_key, None)\n            return \"This Discord Codex channel is pinned to openai-codex (`gpt-5.5`).\"\n\n        # No args: show interactive picker (Telegram/Discord) or text list\n        if not model_input and not explicit_provider:\n""",
        ),
        (
            "                    reasoning_config=reasoning_config,\n                    service_tier=self._service_tier,\n                    request_overrides=turn_route.get(\"request_overrides\"),\n",
            "                    reasoning_config=turn_route.get(\"reasoning_config\", reasoning_config),\n                    service_tier=turn_route.get(\"service_tier\", self._service_tier),\n                    request_overrides=turn_route.get(\"request_overrides\"),\n",
        ),
        (
            "            agent.reasoning_config = reasoning_config\n            agent.service_tier = self._service_tier\n            agent.request_overrides = turn_route.get(\"request_overrides\")\n",
            "            agent.reasoning_config = turn_route.get(\"reasoning_config\", reasoning_config)\n            agent.service_tier = turn_route.get(\"service_tier\", self._service_tier)\n            agent.request_overrides = turn_route.get(\"request_overrides\")\n",
        ),
    ):
        gateway_text = replace_once(gateway_text, old, new, path=gateway_run)
    gateway_text = replace_once(
        gateway_text,
        "    async def _session_expiry_watcher(self, interval: int = 300):\n",
        '''    async def _ghostship_discord_thread_is_dead(self, adapter, thread_id: str) -> bool:
        client = getattr(adapter, "_client", None)
        if client is None:
            return False
        try:
            thread_int = int(thread_id)
        except (TypeError, ValueError):
            return False
        try:
            thread = client.get_channel(thread_int)
            if thread is None:
                thread = await client.fetch_channel(thread_int)
        except Exception:
            return True
        if thread is None:
            return True
        return bool(getattr(thread, "archived", False) or getattr(thread, "locked", False))

    @staticmethod
    def _ghostship_discord_thread_id_for_entry(session_key: str, entry) -> str | None:
        origin = getattr(entry, "origin", None)
        thread_id = getattr(origin, "thread_id", None)
        if thread_id:
            return str(thread_id)
        parsed = _parse_session_key(session_key)
        if parsed and parsed.get("platform") == "discord" and parsed.get("chat_type") == "thread":
            return parsed.get("thread_id") or parsed.get("chat_id")
        return None

    async def _ghostship_retire_closed_discord_threads(self) -> int:
        now = datetime.now()
        if now.hour < 5:
            return 0
        marker = now.date().isoformat()
        if getattr(self, "_ghostship_last_discord_thread_retire_date", None) == marker:
            return 0
        adapter = self.adapters.get(Platform.DISCORD)
        if adapter is None:
            return 0

        self.session_store._ensure_loaded()
        retired = 0
        for key, entry in list(self.session_store._entries.items()):
            platform = getattr(entry, "platform", None)
            platform_value = getattr(platform, "value", platform)
            if platform_value != "discord":
                continue
            if getattr(entry, "chat_type", None) != "thread":
                continue
            if key in self._running_agents:
                continue
            active_processes = getattr(self.session_store, "_has_active_processes_fn", None)
            if active_processes is not None:
                try:
                    if active_processes(key):
                        continue
                except Exception as exc:
                    logger.debug("Discord thread retirement process check failed for %s: %s", key, exc)
                    continue
            thread_id = self._ghostship_discord_thread_id_for_entry(key, entry)
            if not thread_id:
                continue
            if not await self._ghostship_discord_thread_is_dead(adapter, thread_id):
                continue
            if not getattr(entry, "memory_flushed", False):
                try:
                    await self._async_flush_memories(entry.session_id, key)
                except Exception as exc:
                    logger.debug("Discord thread retirement memory flush failed for %s: %s", key, exc)

            cached_agent = None
            cache_lock = getattr(self, "_agent_cache_lock", None)
            if cache_lock is not None:
                with cache_lock:
                    cached = self._agent_cache.get(key)
                    cached_agent = cached[0] if isinstance(cached, tuple) else cached if cached else None
            if cached_agent and cached_agent is not _AGENT_PENDING_SENTINEL:
                self._cleanup_agent_resources(cached_agent)
            self._evict_cached_agent(key)
            self._session_model_overrides.pop(key, None)

            with self.session_store._lock:
                if self.session_store._entries.get(key) is entry:
                    self.session_store._entries.pop(key, None)
                    self.session_store._save()
                    retired += 1

        self._ghostship_last_discord_thread_retire_date = marker
        if retired:
            logger.info("Retired %d closed Discord thread session(s)", retired)
        return retired

    async def _session_expiry_watcher(self, interval: int = 300):
''',
        path=gateway_run,
    )
    gateway_text = replace_once(
        gateway_text,
        '''                # Periodically prune stale SessionStore entries.  The
                # in-memory dict (and sessions.json) would otherwise grow
''',
        '''                try:
                    await self._ghostship_retire_closed_discord_threads()
                except Exception as _e:
                    logger.debug("Discord closed-thread retirement failed: %s", _e)

                # Periodically prune stale SessionStore entries.  The
                # in-memory dict (and sessions.json) would otherwise grow
''',
        path=gateway_run,
    )
    gateway_run.write_text(gateway_text, encoding="utf-8")

    discord_platform = root / "gateway" / "platforms" / "discord.py"
    discord_text = discord_platform.read_text(encoding="utf-8")
    for old, new in (
        (
            "        thread_id = None\n\n        if is_dm:\n",
            "        thread_id = None\n        parent_channel_id = self._get_parent_channel_id(interaction.channel) if is_thread else None\n\n        if is_dm:\n",
        ),
        (
            "            thread_id=thread_id,\n            chat_topic=chat_topic,\n",
            "            thread_id=thread_id,\n            chat_id_alt=parent_channel_id,\n            chat_topic=chat_topic,\n",
        ),
        (
            "        source = self.build_source(\n            chat_id=thread_id,\n",
            "        _parent_channel = self._thread_parent_channel(getattr(interaction, \"channel\", None))\n        _parent_id = str(getattr(_parent_channel, \"id\", \"\") or \"\")\n\n        source = self.build_source(\n            chat_id=thread_id,\n",
        ),
        (
            "            thread_id=thread_id,\n            chat_topic=chat_topic,\n        )\n\n        _parent_channel = self._thread_parent_channel(getattr(interaction, \"channel\", None))\n        _parent_id = str(getattr(_parent_channel, \"id\", \"\") or \"\")\n",
            "            thread_id=thread_id,\n            chat_id_alt=_parent_id or None,\n            chat_topic=chat_topic,\n        )\n\n",
        ),
        (
            "            skip_thread = bool(channel_ids & no_thread_channels) or is_free_channel\n",
            "            skip_thread = bool(channel_ids & no_thread_channels)\n",
        ),
        (
            "                    thread_id = str(thread.id)\n                    auto_threaded_channel = thread\n",
            "                    thread_id = str(thread.id)\n                    parent_channel_id = str(message.channel.id)\n                    auto_threaded_channel = thread\n",
        ),
        (
            "            thread_id=thread_id,\n            chat_topic=chat_topic,\n            is_bot=getattr(message.author, \"bot\", False),\n",
            "            thread_id=thread_id,\n            chat_id_alt=parent_channel_id if is_thread else None,\n            chat_topic=chat_topic,\n            is_bot=getattr(message.author, \"bot\", False),\n",
        ),
    ):
        discord_text = replace_once(discord_text, old, new, path=discord_platform)
    discord_platform.write_text(discord_text, encoding="utf-8")

    webhook_cli = root / "hermes_cli" / "webhook.py"
    webhook_text = webhook_cli.read_text(encoding="utf-8")
    webhook_text = replace_once(
        webhook_text,
        '    if args.deliver_chat_id:\n        route["deliver_extra"] = {"chat_id": args.deliver_chat_id}\n',
        '    deliver_chat_id = args.deliver_chat_id\n    if not deliver_chat_id and route["deliver"] == "discord":\n        deliver_chat_id = os.getenv("DISCORD_WEBHOOK_CHANNEL", "").strip()\n    if deliver_chat_id:\n        route["deliver_extra"] = {"chat_id": deliver_chat_id}\n',
        path=webhook_cli,
    )
    webhook_cli.write_text(webhook_text, encoding="utf-8")

    app_tsx = root / "web" / "src" / "App.tsx"
    app_text = app_tsx.read_text(encoding="utf-8")
    if 'const BUILTIN_ROUTES: Record<string, React.ComponentType> = {' in app_text:
        app_text = replace_once(
            app_text,
            '  Terminal,\n  Globe,\n',
            '  Terminal,\n  TerminalSquare,\n  Globe,\n',
            path=app_tsx,
        )
        app_text = replace_once(
            app_text,
            'import CronPage from "@/pages/CronPage";\n',
            'import CronPage from "@/pages/CronPage";\nimport ConsolePage from "@/pages/ConsolePage";\n',
            path=app_tsx,
        )
        app_text = replace_once(
            app_text,
            '  "/env": EnvPage,\n};\n',
            '  "/env": EnvPage,\n  "/console": ConsolePage,\n};\n',
            path=app_tsx,
        )
        app_text = replace_once(
            app_text,
            '  { path: "/env", labelKey: "keys", label: "Keys", icon: KeyRound },\n];\n',
            '  { path: "/env", labelKey: "keys", label: "Keys", icon: KeyRound },\n  { path: "/console", label: "Terminal", icon: TerminalSquare },\n];\n',
            path=app_tsx,
        )
    elif 'const BUILTIN_NAV: NavItem[] = [' in app_text:
        app_text = replace_once(
            app_text,
            """import {\n  Activity, BarChart3, Clock, FileText, KeyRound,\n  MessageSquare, Package, Settings, Puzzle,\n  Sparkles, Terminal, Globe, Database, Shield,\n  Wrench, Zap, Heart, Star, Code, Eye,\n} from \"lucide-react\";\n""",
            """import {\n  Activity, BarChart3, Clock, FileText, KeyRound,\n  MessageSquare, Package, Settings, Puzzle,\n  Sparkles, Terminal, TerminalSquare, Globe, Database, Shield,\n  Wrench, Zap, Heart, Star, Code, Eye,\n} from \"lucide-react\";\n""",
            path=app_tsx,
        )
        app_text = replace_once(
            app_text,
            'import CronPage from "@/pages/CronPage";\n',
            'import CronPage from "@/pages/CronPage";\nimport ConsolePage from "@/pages/ConsolePage";\n',
            path=app_tsx,
        )
        app_text = replace_once(
            app_text,
            '  { path: "/env", labelKey: "keys", label: "Keys", icon: KeyRound },\n];\n',
            '  { path: "/env", labelKey: "keys", label: "Keys", icon: KeyRound },\n  { path: "/console", label: "Terminal", icon: TerminalSquare },\n];\n',
            path=app_tsx,
        )
        app_text = replace_once(
            app_text,
            '          <Route path="/env" element={<EnvPage />} />\n',
            '          <Route path="/env" element={<EnvPage />} />\n          <Route path="/console" element={<ConsolePage />} />\n',
            path=app_tsx,
        )
    else:
        app_text = replace_once(
            app_text,
            'import { Activity, BarChart3, Clock, FileText, KeyRound, MessageSquare, Package, Settings } from "lucide-react";\n',
            'import { Activity, BarChart3, Clock, FileText, KeyRound, MessageSquare, Package, Settings, TerminalSquare } from "lucide-react";\n',
            path=app_tsx,
        )
        app_text = replace_once(
            app_text,
            'import CronPage from "@/pages/CronPage";\n',
            'import CronPage from "@/pages/CronPage";\nimport ConsolePage from "@/pages/ConsolePage";\n',
            path=app_tsx,
        )
        app_text = replace_once(
            app_text,
            '  { id: "env", label: "Keys", icon: KeyRound },\n] as const;\n',
            '  { id: "env", label: "Keys", icon: KeyRound },\n  { id: "console", label: "Terminal", icon: TerminalSquare },\n] as const;\n',
            path=app_tsx,
        )
        app_text = replace_once(
            app_text,
            '  env: EnvPage,\n};\n',
            '  env: EnvPage,\n  console: ConsolePage,\n};\n',
            path=app_tsx,
        )
    app_tsx.write_text(app_text, encoding="utf-8")

    console_page = root / "web" / "src" / "pages" / "ConsolePage.tsx"
    console_page.write_text(CONSOLE_PAGE, encoding="utf-8")


if __name__ == "__main__":
    main()
