from __future__ import annotations

from typer.testing import CliRunner

from ghostship_plex import cli


runner = CliRunner()


class DummyClient:
    def __init__(self):
        self.calls = []

    def get_identity(self, *, timeout=None):
        self.calls.append(('get_identity', timeout))
        return {'ok': True}

    def build_request(self, method, path, *, params=None, json_data=None):
        class _Spec:
            def __init__(self, payload): self.payload = payload
            def to_dict(self): return self.payload
        return _Spec({'method': method, 'path': path, 'params': params, 'json_body': json_data, 'timeout': 30})

    def build_terminate_session(self, session_id):
        return self.build_request('PUT', f'library/terminate/{session_id}')

    def terminate_session(self, session_id, *, timeout=None):
        self.calls.append(('terminate_session', session_id, timeout))
        return {'ok': True}


def test_timeout_applies(monkeypatch):
    client = DummyClient()
    monkeypatch.setattr(cli, 'get_client', lambda: client)
    result = runner.invoke(cli.app, ['--timeout', '8', 'get_identity'])
    assert result.exit_code == 0
    assert client.calls[-1] == ('get_identity', 8.0)


def test_terminate_session_dry_run(monkeypatch):
    client = DummyClient()
    monkeypatch.setattr(cli, 'get_client', lambda: client)
    result = runner.invoke(cli.app, ['terminate_session', '4', '--dry-run'])
    assert result.exit_code == 0
    assert 'library/terminate/4' in result.stdout
    assert not client.calls
