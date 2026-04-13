from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any
from urllib import error, request

DISCORD_API_BASE = "https://discord.com/api/v10"
MODEL_CACHE_TTL_SECONDS = 60.0
WARNING_HEADER = "**🚨 ROUTER-ONLY CHANNEL 🚨**"
STATE_FILENAME = "state.json"


def _hermes_home() -> Path:
    raw = os.environ.get("HERMES_HOME")
    if raw:
        return Path(raw).expanduser()
    return Path.home() / ".hermes"


def _hook_dir() -> Path:
    return Path(__file__).resolve().parent


def _state_path() -> Path:
    return _hook_dir() / STATE_FILENAME


def _sessions_path() -> Path:
    return _hermes_home() / "sessions" / "sessions.json"


def _router_channel() -> str:
    return os.environ.get("GHOSTSHIP_ROUTER_CHANNEL", "").strip()


def _router_base_url() -> str:
    return os.environ.get("GHOSTSHIP_ROUTER_BASE_URL", "http://127.0.0.1:8788/v1").rstrip("/")


def _load_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return default
    except Exception:
        return default


def _load_state() -> dict[str, Any]:
    state = _load_json(_state_path(), {})
    if not isinstance(state, dict):
        return {}
    return state


def _save_state(state: dict[str, Any]) -> None:
    path = _state_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(state, indent=2, sort_keys=True), encoding='utf-8')
    tmp.replace(path)


def _load_sessions() -> dict[str, Any]:
    data = _load_json(_sessions_path(), {})
    if isinstance(data, dict):
        return data
    return {}


def _find_session_by_id(session_id: str) -> tuple[str | None, dict[str, Any] | None]:
    for session_key, entry in _load_sessions().items():
        if isinstance(entry, dict) and entry.get('session_id') == session_id:
            return session_key, entry
    return None, None


def _find_session_by_key(session_key: str) -> dict[str, Any] | None:
    entry = _load_sessions().get(session_key)
    return entry if isinstance(entry, dict) else None


def _find_recent_router_channel_session(platform: str, user_id: str) -> tuple[str | None, dict[str, Any] | None]:
    target_channel = _router_channel()
    newest_key = None
    newest_entry = None
    newest_updated = ""
    for session_key, entry in _load_sessions().items():
        if not isinstance(entry, dict):
            continue
        origin = entry.get('origin') or {}
        if origin.get('platform') != platform:
            continue
        if str(origin.get('chat_id') or '') != target_channel:
            continue
        if str(origin.get('user_id') or '') != str(user_id or ''):
            continue
        updated_at = str(entry.get('updated_at') or '')
        if updated_at >= newest_updated:
            newest_key = session_key
            newest_entry = entry
            newest_updated = updated_at
    return newest_key, newest_entry


def _is_router_channel_entry(entry: dict[str, Any] | None) -> bool:
    if not entry:
        return False
    origin = entry.get('origin') or {}
    return str(origin.get('platform') or '') == 'discord' and str(origin.get('chat_id') or '') == _router_channel()


def _post_discord_message(channel_id: str, content: str) -> None:
    token = os.environ.get('DISCORD_BOT_TOKEN', '').strip()
    if not token or not channel_id:
        return
    payload = json.dumps({'content': content}).encode('utf-8')
    req = request.Request(
        f"{DISCORD_API_BASE}/channels/{channel_id}/messages",
        data=payload,
        headers={
            'Authorization': f'Bot {token}',
            'Content-Type': 'application/json',
        },
        method='POST',
    )
    try:
        with request.urlopen(req, timeout=10):
            return
    except error.URLError:
        return


def _fetch_router_models(force_refresh: bool = False) -> list[str]:
    state = _load_state()
    cache = state.get('models_cache') if isinstance(state.get('models_cache'), dict) else {}
    now = time.time()
    if not force_refresh:
        fetched_at = float(cache.get('fetched_at') or 0)
        models = cache.get('models')
        if fetched_at and (now - fetched_at) < MODEL_CACHE_TTL_SECONDS and isinstance(models, list):
            return [str(model) for model in models if str(model).strip()]

    req = request.Request(
        f"{_router_base_url()}/models",
        headers={'Accept': 'application/json'},
        method='GET',
    )
    models: list[str] = []
    try:
        with request.urlopen(req, timeout=5) as response:
            payload = json.loads(response.read().decode('utf-8'))
        for item in payload.get('data', []):
            if isinstance(item, dict) and item.get('id'):
                models.append(str(item['id']))
    except Exception:
        models = [str(model) for model in cache.get('models', []) if str(model).strip()]

    state['models_cache'] = {'fetched_at': now, 'models': models}
    _save_state(state)
    return models


def _parse_model_command(args: str) -> tuple[str | None, str | None]:
    tokens = (args or '').split()
    if not tokens:
        return None, None
    provider = None
    model = None
    idx = 0
    while idx < len(tokens):
        token = tokens[idx]
        if token == '--provider' and idx + 1 < len(tokens):
            provider = tokens[idx + 1]
            idx += 2
            continue
        if token.startswith('--provider='):
            provider = token.split('=', 1)[1]
            idx += 1
            continue
        if token.startswith('--'):
            idx += 1
            continue
        if model is None:
            model = token
        idx += 1
    if model and model.startswith('custom:'):
        parts = model.split(':', 2)
        if len(parts) == 3:
            return parts[1], parts[2]
    return provider, model


def _track_model_selection(context: dict[str, Any]) -> None:
    platform = str(context.get('platform') or '')
    user_id = str(context.get('user_id') or '')
    if platform != 'discord' or not user_id or not _router_channel():
        return
    session_key, entry = _find_recent_router_channel_session(platform, user_id)
    if not session_key or not entry:
        return
    provider, model = _parse_model_command(str(context.get('args') or ''))
    state = _load_state()
    session_models = state.setdefault('session_models', {})
    warned_sessions = state.setdefault('warned_sessions', {})
    session_id = str(entry.get('session_id') or '')
    if provider == 'ghostship-router' and model:
        models = _fetch_router_models(force_refresh=True)
        if model in models:
            session_models[session_id] = {
                'provider': provider,
                'model': model,
                'updated_at': time.time(),
            }
            warned_sessions.pop(session_id, None)
        else:
            session_models.pop(session_id, None)
    elif model or provider:
        session_models.pop(session_id, None)
    _save_state(state)


def _warning_message(models: list[str]) -> str:
    lines = [
        WARNING_HEADER,
        '',
        'This Discord channel is reserved for Ghostship Router free-model sessions.',
        'Switch with one of these commands before continuing:',
        '',
        '```text',
    ]
    for model in models:
        lines.append(f'/model custom:ghostship-router:{model}')
    lines.append('```')
    return "\n".join(lines)


def _warning_target(entry: dict[str, Any]) -> str:
    origin = entry.get('origin') or {}
    return str(origin.get('thread_id') or origin.get('chat_id') or '')


def _session_uses_router_model(session_id: str, models: list[str]) -> bool:
    state = _load_state()
    session_models = state.get('session_models') if isinstance(state.get('session_models'), dict) else {}
    current = session_models.get(session_id)
    if not isinstance(current, dict):
        return False
    return current.get('provider') == 'ghostship-router' and str(current.get('model') or '') in models


def _mark_warned(session_id: str) -> None:
    state = _load_state()
    warned_sessions = state.setdefault('warned_sessions', {})
    warned_sessions[session_id] = time.time()
    _save_state(state)


def _has_warned(session_id: str) -> bool:
    state = _load_state()
    warned_sessions = state.get('warned_sessions') if isinstance(state.get('warned_sessions'), dict) else {}
    return session_id in warned_sessions


def _clear_session_tracking(session_id: str) -> None:
    state = _load_state()
    session_models = state.setdefault('session_models', {})
    warned_sessions = state.setdefault('warned_sessions', {})
    session_models.pop(session_id, None)
    warned_sessions.pop(session_id, None)
    _save_state(state)


def _maybe_warn(session_id: str, *, force: bool = False) -> None:
    if not session_id or not _router_channel():
        return
    _, entry = _find_session_by_id(session_id)
    if not _is_router_channel_entry(entry):
        return
    models = _fetch_router_models()
    if not models:
        return
    if _session_uses_router_model(session_id, models):
        return
    if not force and _has_warned(session_id):
        return
    _post_discord_message(_warning_target(entry), _warning_message(models))
    _mark_warned(session_id)


async def handle(event_type: str, context: dict[str, Any] | None = None) -> None:
    context = context or {}
    if event_type == 'command:model':
        _track_model_selection(context)
        return

    if str(context.get('platform') or '') != 'discord':
        return

    if event_type == 'agent:start':
        _maybe_warn(str(context.get('session_id') or ''))
        return

    if event_type == 'session:reset':
        session_key = str(context.get('session_key') or '')
        entry = _find_session_by_key(session_key)
        if not _is_router_channel_entry(entry):
            return
        session_id = str(entry.get('session_id') or '')
        _clear_session_tracking(session_id)
        _maybe_warn(session_id, force=True)
