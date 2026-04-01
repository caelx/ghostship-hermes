from __future__ import annotations

from typer.testing import CliRunner

from ghostship_searxng import cli


runner = CliRunner()


class DummyClient:
    def __init__(self):
        self.calls = []

    def build_request(self, path, *, params=None):
        class _Spec:
            def __init__(self, payload): self.payload = payload
            def to_dict(self): return self.payload
        return _Spec({'path': path, 'params': params})

    def request(self, path, *, params=None, timeout=None):
        self.calls.append(('request', path, params, timeout))
        return {'ok': True}

    def search_web(self, **kwargs):
        self.calls.append(('search_web', kwargs))
        return {'ok': True}


def test_request_dry_run(monkeypatch):
    client = DummyClient()
    monkeypatch.setattr(cli, 'get_client', lambda base_url=None: client)
    result = runner.invoke(cli.app, ['request', 'search', '--param', 'q=test', '--dry-run'])
    assert result.exit_code == 0
    assert 'search' in result.stdout
    assert not client.calls


def test_timeout_applies(monkeypatch):
    client = DummyClient()
    monkeypatch.setattr(cli, 'get_client', lambda base_url=None: client)
    result = runner.invoke(cli.app, ['--timeout', '7', 'search_web', 'query'])
    assert result.exit_code == 0
    assert client.calls[-1][0] == 'search_web'
    assert client.calls[-1][1]['timeout'] == 7.0
