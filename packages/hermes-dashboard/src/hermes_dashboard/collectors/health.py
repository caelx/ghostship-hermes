"""Health check collector for keys and services."""

from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from .runtime import gateway_service_probe
from .utils import default_hermes_dir, default_projects_dir


@dataclass
class KeyStatus:
    name: str
    source: str
    present: bool = False
    note: str = ''
    required: bool = True


@dataclass
class ServiceStatus:
    name: str
    running: bool = False
    pid: Optional[int] = None
    note: str = ''


@dataclass
class HealthState:
    keys: list[KeyStatus] = field(default_factory=list)
    services: list[ServiceStatus] = field(default_factory=list)
    config_model: str = ''
    config_provider: str = ''
    hermes_dir_exists: bool = False
    projects_dir: str = ''
    projects_dir_exists: bool = False
    state_db_exists: bool = False
    state_db_size: int = 0

    @property
    def keys_ok(self) -> int:
        return sum(1 for key in self.keys if key.present)

    @property
    def keys_missing(self) -> int:
        return sum(1 for key in self.keys if key.required and not key.present)

    @property
    def services_ok(self) -> int:
        return sum(1 for service in self.services if service.running)

    @property
    def all_healthy(self) -> bool:
        return self.keys_missing == 0 and all(service.running for service in self.services)


EXPECTED_KEYS = [
    ('OPENCODE_GO_API_KEY', 'env', 'Primary model provider', True),
    ('GOOGLE_AI_STUDIO_API_KEY', 'env', 'Auxiliary task provider', True),
    ('OPENROUTER_API_KEY', 'env', 'Optional fallback provider', True),
    ('DISCORD_TOKEN', 'env', 'Messaging gateway bot token', True),
    ('BITWARDENCLI_APPDATA_DIR', 'env', 'Bitwarden CLI state path', True),
]


def _load_dotenv_keys(dotenv_path: str) -> set[str]:
    keys = set()
    try:
        with open(dotenv_path, encoding='utf-8') as handle:
            for line in handle:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key = line.split('=', 1)[0].strip()
                    if key:
                        keys.add(key)
    except (OSError, PermissionError):
        pass
    return keys


def _get_dotenv_keys(hermes_dir: str) -> set[str]:
    keys: set[str] = set()
    for env_path in [os.path.join(hermes_dir, '.env'), os.path.expanduser('~/.env')]:
        keys.update(_load_dotenv_keys(env_path))
    return keys


def _check_env_key(name: str, hermes_dir: str = '', dotenv_keys: set[str] | None = None) -> bool:
    if os.environ.get(name, ''):
        return True
    if hermes_dir and dotenv_keys is not None:
        return name in dotenv_keys
    return False


def _check_process(name: str, pattern: str) -> ServiceStatus:
    try:
        result = subprocess.run(['pgrep', '-f', pattern], capture_output=True, text=True, timeout=5)
        pids = [int(item) for item in result.stdout.strip().split('\n') if item.strip()]
        if pids:
            return ServiceStatus(name=name, running=True, pid=pids[0])
        return ServiceStatus(name=name, running=False)
    except (subprocess.TimeoutExpired, FileNotFoundError, ValueError):
        return ServiceStatus(name=name, running=False, note='check failed')


def _check_pid_file(name: str, pid_file: Path) -> ServiceStatus:
    if not pid_file.exists():
        return ServiceStatus(name=name, running=False, note='no pid file')
    try:
        data = json.loads(pid_file.read_text(encoding='utf-8'))
        pid = data.get('pid')
        if pid:
            result = subprocess.run(['ps', '-p', str(pid), '-o', 'pid='], capture_output=True, text=True, timeout=5)
            if result.returncode == 0 and result.stdout.strip():
                return ServiceStatus(name=name, running=True, pid=pid)
            return ServiceStatus(name=name, running=False, pid=pid, note='pid file exists but process dead')
    except (json.JSONDecodeError, OSError, subprocess.TimeoutExpired):
        pass
    return ServiceStatus(name=name, running=False, note='pid file unreadable')


def collect_health(hermes_dir: str | None = None) -> HealthState:
    if hermes_dir is None:
        hermes_dir = default_hermes_dir(hermes_dir)
    hermes_path = Path(hermes_dir)
    projects_dir = default_projects_dir()
    state = HealthState(projects_dir=projects_dir)
    state.hermes_dir_exists = hermes_path.exists()
    state.projects_dir_exists = Path(projects_dir).exists()

    state_db = hermes_path / 'state.db'
    state.state_db_exists = state_db.exists()
    if state.state_db_exists:
        try:
            state.state_db_size = state_db.stat().st_size
        except OSError:
            pass

    from .config import collect_config

    try:
        config = collect_config(hermes_dir)
        state.config_model = config.model
        state.config_provider = config.provider
    except Exception:
        pass

    dotenv_keys = _get_dotenv_keys(hermes_dir)
    known_names = {key_name for key_name, _, _, _ in EXPECTED_KEYS}
    for key_name, source, note, required in EXPECTED_KEYS:
        present = _check_env_key(key_name, hermes_dir, dotenv_keys)
        state.keys.append(KeyStatus(name=key_name, source=source, present=present, note='' if present else note, required=required))

    for extra_key in sorted(dotenv_keys):
        if extra_key not in known_names and any(extra_key.endswith(suffix) for suffix in ('_API_KEY', '_TOKEN', '_SECRET')):
            state.keys.append(KeyStatus(name=extra_key, source='env', present=True, note='discovered'))

    state.services.append(_check_pid_file('Gateway PID', hermes_path / 'gateway.pid'))
    gateway_probe = gateway_service_probe()
    scope_label = 'user' if gateway_probe.scope == 'user' else 'system'
    state.services.append(
        ServiceStatus(
            name=f'Gateway ({scope_label})',
            running=gateway_probe.active,
            note=f'{gateway_probe.service}: {gateway_probe.note}',
        )
    )
    state.services.append(_check_process('llama-server', 'llama-server'))
    return state
