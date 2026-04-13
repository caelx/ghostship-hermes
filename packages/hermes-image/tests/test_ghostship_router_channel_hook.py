from __future__ import annotations

import asyncio
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
HANDLER_PATH = ROOT / 'packages/hermes-image' / 'hooks' / 'ghostship-router-channel-guidance' / 'handler.py'

spec = importlib.util.spec_from_file_location('ghostship_router_channel_guidance', HANDLER_PATH)
module = importlib.util.module_from_spec(spec)
assert spec is not None and spec.loader is not None
spec.loader.exec_module(module)


def _write_sessions(path: Path, sessions: dict[str, object]) -> None:
    sessions_dir = path / 'sessions'
    sessions_dir.mkdir(parents=True, exist_ok=True)
    (sessions_dir / 'sessions.json').write_text(json.dumps(sessions, indent=2), encoding='utf-8')


def _base_session(session_id: str, *, updated_at: str = '2026-04-12T00:00:00', session_key: str = 'agent:main:discord:channel:1492841053642817606') -> dict[str, object]:
    return {
        session_key: {
            'session_key': session_key,
            'session_id': session_id,
            'created_at': '2026-04-12T00:00:00',
            'updated_at': updated_at,
            'platform': 'discord',
            'chat_type': 'channel',
            'origin': {
                'platform': 'discord',
                'chat_id': '1492841053642817606',
                'chat_name': 'freedom',
                'chat_type': 'channel',
                'user_id': 'user-1',
                'user_name': 'tester',
            },
        }
    }


@pytest.fixture(autouse=True)
def hook_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv('HERMES_HOME', str(tmp_path))
    monkeypatch.setenv('GHOSTSHIP_ROUTER_CHANNEL', '1492841053642817606')
    monkeypatch.setenv('DISCORD_BOT_TOKEN', 'test-bot-token')
    monkeypatch.setenv('GHOSTSHIP_ROUTER_BASE_URL', 'http://router.test/v1')
    state_path = HANDLER_PATH.parent / module.STATE_FILENAME
    if state_path.exists():
        state_path.unlink()


def test_agent_start_warns_with_full_commands(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _write_sessions(tmp_path, _base_session('session-1'))
    sent: list[tuple[str, str]] = []
    monkeypatch.setattr(module, '_fetch_router_models', lambda force_refresh=False: ['agentic', 'coding'])
    monkeypatch.setattr(module, '_post_discord_message', lambda channel_id, content: sent.append((channel_id, content)) or True)

    asyncio.run(module.handle('agent:start', {'platform': 'discord', 'session_id': 'session-1', 'message': 'hi'}))

    assert len(sent) == 1
    channel_id, content = sent[0]
    assert channel_id == '1492841053642817606'
    assert module.WARNING_HEADER in content
    assert '/model custom:ghostship-router:agentic' in content
    assert '/model custom:ghostship-router:coding' in content


def test_router_model_selection_suppresses_warning_until_reset(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    sessions = _base_session('session-1')
    _write_sessions(tmp_path, sessions)
    sent: list[tuple[str, str]] = []
    monkeypatch.setattr(module, '_fetch_router_models', lambda force_refresh=False: ['agentic', 'coding'])
    monkeypatch.setattr(module, '_post_discord_message', lambda channel_id, content: sent.append((channel_id, content)) or True)

    asyncio.run(module.handle('command:model', {
        'platform': 'discord',
        'user_id': 'user-1',
        'command': 'model',
        'args': 'custom:ghostship-router:agentic',
    }))
    asyncio.run(module.handle('agent:start', {'platform': 'discord', 'session_id': 'session-1', 'message': 'hi'}))

    assert sent == []

    sessions['agent:main:discord:channel:1492841053642817606']['session_id'] = 'session-2'
    sessions['agent:main:discord:channel:1492841053642817606']['updated_at'] = '2026-04-12T00:10:00'
    _write_sessions(tmp_path, sessions)

    asyncio.run(module.handle('session:reset', {'platform': 'discord', 'session_key': 'agent:main:discord:channel:1492841053642817606'}))

    assert len(sent) == 1
    assert '/model custom:ghostship-router:agentic' in sent[0][1]


def test_non_router_model_command_clears_tracked_router_session(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _write_sessions(tmp_path, _base_session('session-1'))
    monkeypatch.setattr(module, '_fetch_router_models', lambda force_refresh=False: ['agentic', 'coding'])
    monkeypatch.setattr(module, '_post_discord_message', lambda channel_id, content: True)

    asyncio.run(module.handle('command:model', {
        'platform': 'discord',
        'user_id': 'user-1',
        'command': 'model',
        'args': 'custom:ghostship-router:agentic',
    }))
    asyncio.run(module.handle('command:model', {
        'platform': 'discord',
        'user_id': 'user-1',
        'command': 'model',
        'args': 'gpt-5.4-mini --provider openai-codex',
    }))

    assert module._session_uses_router_model('session-1', ['agentic', 'coding']) is False


def test_failed_post_does_not_suppress_retry(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _write_sessions(tmp_path, _base_session('session-1'))
    monkeypatch.setattr(module, '_fetch_router_models', lambda force_refresh=False: ['agentic'])

    calls: list[tuple[str, str]] = []
    outcomes = iter([False, True])

    def post(channel_id: str, content: str) -> bool:
        calls.append((channel_id, content))
        return next(outcomes)

    monkeypatch.setattr(module, '_post_discord_message', post)

    asyncio.run(module.handle('agent:start', {'platform': 'discord', 'session_id': 'session-1', 'message': 'hi'}))
    asyncio.run(module.handle('agent:start', {'platform': 'discord', 'session_id': 'session-1', 'message': 'again'}))

    assert len(calls) == 2
    assert module._last_warned_at('session-1') > 0


def test_agent_start_rewarns_after_one_minute(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _write_sessions(tmp_path, _base_session('session-1'))
    sent: list[tuple[str, str]] = []
    now = {'value': 1000.0}

    monkeypatch.setattr(module, '_fetch_router_models', lambda force_refresh=False: ['agentic'])
    monkeypatch.setattr(module.time, 'time', lambda: now['value'])
    monkeypatch.setattr(module, '_post_discord_message', lambda channel_id, content: sent.append((channel_id, content)) or True)

    asyncio.run(module.handle('agent:start', {'platform': 'discord', 'session_id': 'session-1', 'message': 'first'}))
    now['value'] += 30.0
    asyncio.run(module.handle('agent:start', {'platform': 'discord', 'session_id': 'session-1', 'message': 'second'}))
    now['value'] += 31.0
    asyncio.run(module.handle('agent:start', {'platform': 'discord', 'session_id': 'session-1', 'message': 'third'}))

    assert len(sent) == 2
