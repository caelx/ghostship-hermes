"""Collect profile data for the HUD."""

from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from urllib.error import URLError
from urllib.parse import urlparse
from urllib.request import urlopen

from ..cache import get_cached_or_compute
from .memory import MEMORY_MAX_CHARS, USER_MAX_CHARS
from .models import ProfileInfo, ProfilesState
from .runtime import default_profile_name, gateway_service_probe
from .utils import default_hermes_dir, safe_get

_ALIAS_BIN_DIRS = [os.path.expanduser('~/.local/bin'), '/usr/local/bin']


def _parse_yaml_simple(text: str) -> dict:
    result = {}
    current_key = None
    for line in text.split('\n'):
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            continue
        if line.startswith('  ') and current_key and ':' in stripped:
            key, _, value = stripped.partition(':')
            value = value.strip().strip("'").strip('"')
            if current_key not in result or not isinstance(result[current_key], dict):
                result[current_key] = {}
            if isinstance(result[current_key], dict):
                result[current_key][key.strip()] = value
        elif line.startswith('- ') and current_key:
            if not isinstance(result.get(current_key), list):
                result[current_key] = []
            result[current_key].append(stripped.lstrip('- ').strip())
        elif ':' in stripped and not stripped.startswith('-'):
            key, _, value = stripped.partition(':')
            key = key.strip()
            value = value.strip().strip("'").strip('"')
            current_key = key
            if value:
                result[key] = value
    return result


def _read_config(profile_dir: Path) -> dict:
    config_path = profile_dir / 'config.yaml'
    if not config_path.exists():
        return {}
    try:
        return _parse_yaml_simple(config_path.read_text(encoding='utf-8'))
    except Exception:
        return {}


def _read_soul_summary(profile_dir: Path) -> str:
    soul_path = profile_dir / 'SOUL.md'
    if not soul_path.exists():
        return ''
    try:
        text = soul_path.read_text(encoding='utf-8')
        for line in text.split('\n'):
            line = line.strip()
            if line and not line.startswith('#') and not line.startswith('---'):
                return line[:117] + '...' if len(line) > 120 else line
        for line in text.split('\n'):
            line = line.strip()
            if line.startswith('# '):
                return line[2:].strip()
        return ''
    except Exception:
        return ''


def _read_memory_stats(profile_dir: Path) -> dict:
    stats = {
        'memory_entries': 0,
        'memory_chars': 0,
        'memory_max_chars': MEMORY_MAX_CHARS,
        'user_entries': 0,
        'user_chars': 0,
        'user_max_chars': USER_MAX_CHARS,
    }
    for fname, prefix in [('MEMORY.md', 'memory'), ('USER.md', 'user')]:
        fpath = profile_dir / 'memories' / fname
        if not fpath.exists():
            continue
        try:
            text = fpath.read_text(encoding='utf-8').strip()
            if text:
                entries = [entry.strip() for entry in text.split('\u00a7') if entry.strip()]
                stats[f'{prefix}_entries'] = len(entries)
                stats[f'{prefix}_chars'] = len(text)
        except Exception:
            pass
    return stats


def _read_session_stats(profile_dir: Path) -> dict:
    stats = {
        'session_count': 0,
        'message_count': 0,
        'tool_call_count': 0,
        'total_input_tokens': 0,
        'total_output_tokens': 0,
        'last_active': None,
    }
    db_path = profile_dir / 'state.db'
    if not db_path.exists():
        return stats
    try:
        conn = sqlite3.connect(str(db_path))
        cur = conn.cursor()
        cur.execute(
            """
            SELECT
                COUNT(*) as cnt,
                COALESCE(SUM(message_count), 0),
                COALESCE(SUM(tool_call_count), 0),
                COALESCE(SUM(input_tokens), 0),
                COALESCE(SUM(output_tokens), 0),
                MAX(started_at)
            FROM sessions
            """
        )
        row = cur.fetchone()
        if row:
            stats['session_count'] = safe_get(row, 0, 0)
            stats['message_count'] = safe_get(row, 1, 0)
            stats['tool_call_count'] = safe_get(row, 2, 0)
            stats['total_input_tokens'] = safe_get(row, 3, 0)
            stats['total_output_tokens'] = safe_get(row, 4, 0)
            last_raw = safe_get(row, 5)
            if last_raw:
                try:
                    stats['last_active'] = datetime.fromtimestamp(float(last_raw))
                except (ValueError, TypeError, OSError):
                    pass
        conn.close()
    except Exception:
        pass
    return stats


def _count_skills(profile_dir: Path) -> int:
    skills_dir = profile_dir / 'skills'
    if not skills_dir.exists():
        return 0
    return sum(1 for _ in skills_dir.rglob('SKILL.md'))


def _count_cron_jobs(profile_dir: Path) -> int:
    jobs_path = profile_dir / 'cron' / 'jobs.json'
    if not jobs_path.exists():
        return 0
    try:
        data = json.loads(jobs_path.read_text(encoding='utf-8'))
        jobs = data.get('jobs', data) if isinstance(data, dict) else data
        return len(jobs) if isinstance(jobs, list) else 0
    except Exception:
        return 0


def _read_api_keys(profile_dir: Path) -> list[str]:
    env_path = profile_dir / '.env'
    if not env_path.exists():
        return []
    keys = []
    try:
        for line in env_path.read_text(encoding='utf-8').split('\n'):
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key_name = line.split('=', 1)[0].strip()
                if key_name and ('KEY' in key_name or 'TOKEN' in key_name or 'SECRET' in key_name):
                    keys.append(key_name)
    except Exception:
        pass
    return keys


def _check_gateway_status(is_default: bool) -> str:
    if is_default:
        return 'active' if gateway_service_probe().active else 'inactive'
    return 'unknown'


def _check_server_status(base_url: str) -> str:
    if not base_url or ('localhost' not in base_url and '127.0.0.1' not in base_url):
        return 'n/a'
    try:
        parsed = urlparse(base_url)
        health_url = f"{parsed.scheme}://{parsed.netloc}/health"
        resp = urlopen(health_url, timeout=2)
        return 'running' if resp.status == 200 else 'stopped'
    except (URLError, OSError, ValueError):
        return 'stopped'


def _collect_single_profile(profile_dir: Path, name: str, is_default: bool = False) -> ProfileInfo:
    config = _read_config(profile_dir)
    model_cfg = config.get('model', {})
    if isinstance(model_cfg, str):
        model_cfg = {'default': model_cfg}
    model = model_cfg.get('default', config.get('model', ''))
    provider = model_cfg.get('provider', config.get('provider', ''))
    base_url = model_cfg.get('base_url', '')
    try:
        context_length = int(model_cfg.get('context_length', 0))
    except (ValueError, TypeError):
        context_length = 0
    display_cfg = config.get('display', {})
    skin = display_cfg.get('skin', '') if isinstance(display_cfg, dict) else ''
    toolsets = config.get('toolsets', [])
    if isinstance(toolsets, str):
        toolsets = [toolsets]
    compression_cfg = config.get('compression', {})
    compression_enabled = False
    compression_model = ''
    if isinstance(compression_cfg, dict):
        enabled = compression_cfg.get('enabled', False)
        compression_enabled = enabled.lower() in ('true', '1', 'yes') if isinstance(enabled, str) else bool(enabled)
        compression_model = compression_cfg.get('summary_model', '')
    memory_cfg = config.get('memory', {})
    memory_max = MEMORY_MAX_CHARS
    user_max = USER_MAX_CHARS
    if isinstance(memory_cfg, dict):
        try:
            memory_max = int(memory_cfg.get('memory_char_limit', MEMORY_MAX_CHARS))
        except (ValueError, TypeError):
            pass
        try:
            user_max = int(memory_cfg.get('user_char_limit', USER_MAX_CHARS))
        except (ValueError, TypeError):
            pass
    memory_stats = _read_memory_stats(profile_dir)
    session_stats = _read_session_stats(profile_dir)
    try:
        port = urlparse(base_url).port if base_url else None
    except Exception:
        port = None
    has_alias = any(Path(directory, name).exists() for directory in _ALIAS_BIN_DIRS) if not is_default else False
    return ProfileInfo(
        name=name,
        is_default=is_default,
        model=model,
        provider=provider,
        base_url=base_url,
        port=port,
        toolsets=toolsets,
        skin=skin,
        context_length=context_length,
        soul_summary=_read_soul_summary(profile_dir),
        session_count=session_stats['session_count'],
        message_count=session_stats['message_count'],
        tool_call_count=session_stats['tool_call_count'],
        total_input_tokens=session_stats['total_input_tokens'],
        total_output_tokens=session_stats['total_output_tokens'],
        last_active=session_stats['last_active'],
        memory_entries=memory_stats['memory_entries'],
        memory_chars=memory_stats['memory_chars'],
        memory_max_chars=memory_max,
        user_entries=memory_stats['user_entries'],
        user_chars=memory_stats['user_chars'],
        user_max_chars=user_max,
        skill_count=_count_skills(profile_dir),
        cron_job_count=_count_cron_jobs(profile_dir),
        api_keys=_read_api_keys(profile_dir),
        gateway_status=_check_gateway_status(is_default),
        server_status=_check_server_status(base_url),
        has_alias=has_alias,
        compression_enabled=compression_enabled,
        compression_model=compression_model,
    )


def _do_collect_profiles(hermes_path: Path) -> ProfilesState:
    profiles = [_collect_single_profile(hermes_path, default_profile_name(), is_default=True)]
    profiles_dir = hermes_path / 'profiles'
    if profiles_dir.is_dir():
        for entry in sorted(profiles_dir.iterdir()):
            if entry.is_dir() and not entry.name.startswith('.'):
                profiles.append(_collect_single_profile(entry, entry.name))
    return ProfilesState(profiles=profiles)


def collect_profiles(hermes_dir: str | None = None) -> ProfilesState:
    if hermes_dir is None:
        hermes_dir = default_hermes_dir()
    hermes_path = Path(hermes_dir)
    paths_to_monitor = [hermes_path]
    profiles_dir = hermes_path / 'profiles'
    if profiles_dir.exists():
        paths_to_monitor.append(profiles_dir)
    return get_cached_or_compute(
        cache_key=f'profiles:{hermes_dir}',
        compute_fn=lambda: _do_collect_profiles(hermes_path),
        dir_paths=paths_to_monitor,
        ttl=45,
    )
