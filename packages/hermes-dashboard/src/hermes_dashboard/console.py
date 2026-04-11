from __future__ import annotations

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
        'GHOSTSHIP_DASHBOARD_STATE_DIR',
        '/home/hermes/.local/state/ghostship-hermes/dashboard',
    )
)
STATE_FILE = STATE_DIR / 'state.json'
LOG_DIR = STATE_DIR / 'logs'
TTYD_HOST = os.environ.get('GHOSTSHIP_TTYD_HOST', '127.0.0.1')
TTYD_PORT_BASE = int(os.environ.get('GHOSTSHIP_TTYD_PORT_BASE', '7682'))
TERMINAL_CWD = os.environ.get('GHOSTSHIP_TERMINAL_CWD', '/home/hermes')
HOME_DIR = os.environ.get('HOME', '/home/hermes')
MANAGED_HERMES_HOME = os.environ.get('HERMES_HOME', '/home/hermes/.hermes')
BASH_PATH = os.environ.get('GHOSTSHIP_BASH') or shutil.which('bash') or '/bin/sh'

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
        return {'next_index': 1, 'active_terminal_id': None, 'sessions': []}
    try:
        payload = json.loads(STATE_FILE.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError):
        return {'next_index': 1, 'active_terminal_id': None, 'sessions': []}
    payload.setdefault('next_index', 1)
    payload.setdefault('active_terminal_id', None)
    payload.setdefault('sessions', [])
    return payload


def save_state(state: dict[str, Any]) -> None:
    ensure_state_dir()
    STATE_FILE.write_text(json.dumps(state, indent=2) + '\n', encoding='utf-8')


def child_pids(pid: int) -> list[int]:
    try:
        children = Path(f'/proc/{pid}/task/{pid}/children').read_text(encoding='utf-8').strip()
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
    for candidate in (f'/proc/{pid}/comm', f'/proc/{pid}/cmdline'):
        try:
            raw = Path(candidate).read_bytes()
        except OSError:
            continue
        if not raw:
            continue
        if candidate.endswith('/cmdline'):
            name = raw.replace(b'\x00', b' ').decode('utf-8', errors='ignore').strip()
            if name:
                return name
        else:
            name = raw.decode('utf-8', errors='ignore').strip()
            if name:
                return name
    return ''


def proc_cwd(pid: int) -> str:
    try:
        cwd = os.readlink(f'/proc/{pid}/cwd')
    except OSError:
        return ''
    if cwd.startswith(HOME_DIR):
        suffix = cwd[len(HOME_DIR):].lstrip('/')
        return f'/home/hermes/{suffix}' if suffix else '/home/hermes'
    return cwd


def session_label(session: dict[str, Any]) -> str:
    ttyd_pid = session['pid']
    shell_pid = child_pids(ttyd_pid)
    if not shell_pid:
        return session['cwd'] or session['label']
    active_pid = deepest_descendant(shell_pid[-1])
    active_name = proc_name(active_pid)
    if active_name:
        try:
            command = shlex.split(active_name)[0] if active_name.strip() else ''
        except ValueError:
            command = active_name.split(' ', 1)[0]
        command_name = Path(command).name
        if command_name and command_name not in {'bash', 'sh'}:
            return command_name
    cwd = proc_cwd(active_pid)
    return cwd or session['cwd'] or session['label']


def prune_dead_sessions(state: dict[str, Any]) -> dict[str, Any]:
    alive_sessions = [session for session in state['sessions'] if process_is_alive(session['pid'])]
    state['sessions'] = alive_sessions
    session_ids = {session['id'] for session in alive_sessions}
    if state['active_terminal_id'] not in session_ids:
        state['active_terminal_id'] = alive_sessions[-1]['id'] if alive_sessions else None
    return state


def available_port(state: dict[str, Any]) -> int:
    used_ports = {session['port'] for session in state['sessions']}
    port = TTYD_PORT_BASE
    while port in used_ports or port_is_open(TTYD_HOST, port):
        port += 1
    return port


def ttyd_command(session: dict[str, Any]) -> list[str]:
    shell_command = f"cd {shlex.quote(TERMINAL_CWD)} && exec {shlex.quote(BASH_PATH)} -l"
    return [
        'ttyd',
        '--writable',
        '-i',
        TTYD_HOST,
        '-p',
        str(session['port']),
        '-t',
        'disableLeaveAlert=true',
        '-t',
        'disableResizeOverlay=true',
        '-t',
        'rendererType=webgl',
        '-t',
        'fontFamily=IBM Plex Mono, monospace',
        '--base-path',
        session['terminal_url'].rstrip('/'),
        BASH_PATH,
        '-lc',
        shell_command,
    ]


def _serialize_session(session: dict[str, Any]) -> dict[str, Any]:
    return {
        'id': session['id'],
        'label': session_label(session),
        'pid': session['pid'],
        'port': session['port'],
        'terminal_url': session['terminal_url'],
        'cwd': session['cwd'],
        'ready': port_is_open(TTYD_HOST, session['port']),
    }


def console_payload(state: dict[str, Any]) -> dict[str, Any]:
    sessions = [_serialize_session(session) for session in state['sessions']]
    active_session_id = state.get('active_terminal_id')
    active_session = next((session for session in sessions if session['id'] == active_session_id), None)
    if active_session is None and sessions:
        active_session = sessions[-1]
        active_session_id = active_session['id']
    return {
        'terminal_cwd': TERMINAL_CWD,
        'home': HOME_DIR,
        'managed_hermes_home': MANAGED_HERMES_HOME,
        'active_session_id': active_session_id,
        'session': active_session,
        'sessions': sessions,
    }


async def get_console_status() -> dict[str, Any]:
    async with state_lock:
        state = prune_dead_sessions(load_state())
        save_state(state)
        return console_payload(state)


async def open_console_session() -> dict[str, Any]:
    async with state_lock:
        state = prune_dead_sessions(load_state())
        if state['sessions']:
            if not state.get('active_terminal_id'):
                state['active_terminal_id'] = state['sessions'][-1]['id']
            save_state(state)
            return console_payload(state)

        label = f"Console {state['next_index']}"
        session_id = uuid.uuid4().hex[:10]
        session = {
            'id': session_id,
            'label': label,
            'port': available_port(state),
            'cwd': TERMINAL_CWD,
            'terminal_url': f'/terminals/{session_id}/',
            'started_at': int(time.time()),
        }
        log_path = LOG_DIR / f'{session_id}.log'
        with log_path.open('ab') as log_handle:
            process = subprocess.Popen(
                ttyd_command(session),
                cwd=TERMINAL_CWD,
                env=os.environ.copy(),
                stdout=log_handle,
                stderr=log_handle,
                start_new_session=True,
            )

        await asyncio.sleep(0.15)
        if process.poll() is not None:
            raise RuntimeError(f'ttyd exited during startup with code {process.returncode}')

        session['pid'] = process.pid
        state['next_index'] += 1
        state['sessions'] = [session]
        state['active_terminal_id'] = session_id
        save_state(state)
        return console_payload(state)


def terminate_session(session: dict[str, Any], timeout: float = 0.75) -> None:
    pid = session.get('pid')
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
        session = next((entry for entry in state['sessions'] if entry['id'] == session_id), None)
        if session is None:
            save_state(state)
            return console_payload(state)
        terminate_session(session)
        state['sessions'] = [entry for entry in state['sessions'] if entry['id'] != session_id]
        if state.get('active_terminal_id') == session_id:
            state['active_terminal_id'] = state['sessions'][-1]['id'] if state['sessions'] else None
        save_state(state)
        return console_payload(state)


def get_console_session(session_id: str) -> dict[str, Any] | None:
    state = prune_dead_sessions(load_state())
    for session in state['sessions']:
        if session['id'] == session_id:
            return session
    return None


async def proxy_terminal_http(request: Request, session_id: str, path: str):
    session = get_console_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail='Console session not found')

    url = f"http://{TTYD_HOST}:{session['port']}/terminals/{session_id}/{path}"
    if request.url.query:
        url += f'?{request.url.query}'

    client = httpx.AsyncClient()
    headers = dict(request.headers)
    headers.pop('host', None)
    headers.pop('connection', None)
    headers.pop('keep-alive', None)

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
        raise HTTPException(status_code=503, detail='Console is starting') from exc

    async def stream_response():
        async for chunk in resp.aiter_bytes():
            yield chunk

    async def close_upstream() -> None:
        await resp.aclose()
        await client.aclose()

    response_headers = dict(resp.headers)
    response_headers.pop('content-encoding', None)
    response_headers.pop('transfer-encoding', None)
    response_headers.pop('content-length', None)

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
        target_url += f'?{websocket.url.query}'

    requested_subprotocols = [
        value.strip()
        for value in websocket.headers.get('sec-websocket-protocol', '').split(',')
        if value.strip()
    ]

    try:
        async with websockets.connect(target_url, subprotocols=requested_subprotocols or None) as upstream_ws:
            await websocket.accept(subprotocol=upstream_ws.subprotocol)

            async def forward_to_upstream() -> None:
                while True:
                    data = await websocket.receive()
                    if data.get('type') == 'websocket.disconnect':
                        break
                    if 'text' in data:
                        await upstream_ws.send(data['text'])
                    elif 'bytes' in data:
                        await upstream_ws.send(data['bytes'])

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
