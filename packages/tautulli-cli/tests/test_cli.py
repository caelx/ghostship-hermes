from __future__ import annotations

from typer.testing import CliRunner

from ghostship_tautulli import cli


runner = CliRunner()


class DummyClient:
    def __init__(self):
        self.calls = []

    def get_server_status(self, *, timeout=None):
        self.calls.append(('get_server_status', timeout))
        return {'ok': True}

    def build_terminate_session(self, session_id: str, message: str | None = None):
        class _Spec:
            def __init__(self, payload): self.payload = payload
            def to_dict(self): return self.payload
        return _Spec({'params': {'cmd': 'terminate_session', 'session_id': session_id, 'message': message}})

    def terminate_session(self, session_id: str, message: str | None = None, *, timeout=None):
        self.calls.append(('terminate_session', session_id, message, timeout))
        return {'ok': True}


def test_timeout_applies(monkeypatch):
    client = DummyClient()
    monkeypatch.setattr(cli, 'get_client', lambda: client)
    result = runner.invoke(cli.app, ['--timeout', '8', 'get_server_status'])
    assert result.exit_code == 0
    assert client.calls[-1] == ('get_server_status', 8.0)


def test_terminate_session_dry_run(monkeypatch):
    client = DummyClient()
    monkeypatch.setattr(cli, 'get_client', lambda: client)
    result = runner.invoke(cli.app, ['terminate_session', 'abc', '--message', 'bye', '--dry-run'])
    assert result.exit_code == 0
    assert 'terminate_session' in result.stdout
    assert not client.calls
