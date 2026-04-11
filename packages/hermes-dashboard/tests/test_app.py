from __future__ import annotations

import importlib
from pathlib import Path

from fastapi.testclient import TestClient


def _load_app_module(monkeypatch, tmp_path: Path):
    managed_home = tmp_path / '.hermes'
    managed_home.mkdir(parents=True)
    (managed_home / 'config.yaml').write_text(
        """model:
  provider: opencode-go
  default: minimax-m2.7
fallback_model:
  provider: custom
  model: agentic
  base_url: http://127.0.0.1:8788/v1
""",
        encoding='utf-8',
    )
    (managed_home / '.env').write_text('OPENAI_API_KEY=test-token\nOPENCODE_GO_API_KEY=test-go\n', encoding='utf-8')
    (managed_home / 'SOUL.md').write_text('seeded soul\n', encoding='utf-8')
    (managed_home / 'gateway.pid').write_text('{"pid":123,"kind":"hermes-gateway"}\n', encoding='utf-8')
    projects_dir = tmp_path / 'workspace'
    (projects_dir / 'demo').mkdir(parents=True)
    (projects_dir / 'demo' / 'README.md').write_text('demo\n', encoding='utf-8')

    monkeypatch.setenv('HOME', str(tmp_path))
    monkeypatch.setenv('HERMES_HOME', str(managed_home))
    monkeypatch.setenv('HERMES_HUD_PROJECTS_DIR', str(projects_dir))
    monkeypatch.setenv('GHOSTSHIP_DASHBOARD_STATE_DIR', str(tmp_path / 'state'))
    monkeypatch.setenv('GHOSTSHIP_HERMES_GATEWAY_SERVICE', 'ghostship-hermes-gateway.service')
    monkeypatch.setenv('GHOSTSHIP_HUD_DEFAULT_PROFILE_NAME', 'Managed Agent')
    monkeypatch.setenv('GHOSTSHIP_TERMINAL_CWD', '/workspace')
    monkeypatch.setenv('GHOSTSHIP_HUD_DISABLE_WATCHER', '1')

    import hermes_dashboard.app as app_module
    import hermes_dashboard.collectors.runtime as runtime_module

    runtime_module = importlib.reload(runtime_module)
    app_module = importlib.reload(app_module)
    return app_module, runtime_module


def test_projects_api_reports_workspace_root(monkeypatch, tmp_path: Path) -> None:
    app_module, _runtime_module = _load_app_module(monkeypatch, tmp_path)
    client = TestClient(app_module.app)
    response = client.get('/api/projects')
    assert response.status_code == 200
    payload = response.json()
    assert payload['projects_dir'] == str(tmp_path / 'workspace')
    assert any(project['name'] == 'demo' for project in payload['projects'])


def test_profiles_api_reports_managed_agent(monkeypatch, tmp_path: Path) -> None:
    app_module, runtime_module = _load_app_module(monkeypatch, tmp_path)
    runtime_module.gateway_service_probe = lambda: runtime_module.ServiceProbe(service='ghostship-hermes-gateway.service', scope=None, active=True, note='active')

    import hermes_dashboard.collectors.profiles as profiles_module

    profiles_module = importlib.reload(profiles_module)
    profiles_module.gateway_service_probe = runtime_module.gateway_service_probe

    client = TestClient(app_module.app)
    response = client.get('/api/profiles')
    assert response.status_code == 200
    payload = response.json()
    assert payload['total'] == 1
    assert payload['profiles'][0]['name'] == 'Managed Agent'
    assert payload['profiles'][0]['gateway_status'] == 'active'


def test_console_routes_open_and_close_session(monkeypatch, tmp_path: Path) -> None:
    app_module, _runtime_module = _load_app_module(monkeypatch, tmp_path)
    import hermes_dashboard.console as console_module

    class DummyProcess:
        def __init__(self) -> None:
            self.pid = 4242

        def poll(self):
            return None

    monkeypatch.setattr(console_module.subprocess, 'Popen', lambda *args, **kwargs: DummyProcess())
    monkeypatch.setattr(console_module, 'port_is_open', lambda host, port, timeout=0.15: True)
    monkeypatch.setattr(console_module, 'process_is_alive', lambda pid: True)
    monkeypatch.setattr(console_module, 'terminate_session', lambda session, timeout=0.75: None)

    client = TestClient(app_module.app)
    opened = client.post('/api/console/open')
    assert opened.status_code == 200
    payload = opened.json()
    assert payload['session']['cwd'] == '/workspace'
    assert payload['session']['terminal_url'].startswith('/terminals/')

    session_id = payload['session']['id']
    closed = client.post(f'/api/console/sessions/{session_id}/close')
    assert closed.status_code == 200
    assert closed.json()['session'] is None
