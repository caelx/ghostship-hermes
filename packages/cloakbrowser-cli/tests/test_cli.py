from __future__ import annotations

from typer.testing import CliRunner

from ghostship_cloakbrowser import cli


runner = CliRunner()


class DummyClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple[object, ...], dict[str, object]]] = []

    def get_system_status(self, *, timeout=None):
        self.calls.append(('get_system_status', (), {'timeout': timeout}))
        return {'status': 'ok'}

    def build_request(self, method: str, path: str, *, params=None, json_data=None):
        class _Spec:
            def __init__(self, payload):
                self.payload = payload
            def to_dict(self):
                return self.payload
        return _Spec({'method': method, 'path': path, 'params': params, 'json_body': json_data, 'timeout': 9})

    def request(self, method: str, path: str, *, params=None, json_data=None, timeout=None):
        self.calls.append(('request', (method, path), {'params': params, 'json_data': json_data, 'timeout': timeout}))
        return {'method': method, 'path': path}

    def build_create_profile(self, **kwargs):
        return self.build_request('POST', '/api/profiles', json_data=kwargs)

    def create_profile(self, *, timeout=None, **kwargs):
        self.calls.append(('create_profile', (), {'kwargs': kwargs, 'timeout': timeout}))
        return {'id': 'demo'}


def test_root_help_explains_static_token_auth() -> None:
    result = runner.invoke(cli.app, ['--help'])
    assert result.exit_code == 0
    assert 'CLOAKBROWSER_URL' in result.stdout
    assert 'CLOAKBROWSER_TOKEN' in result.stdout
    assert 'AUTH_TOKEN' in result.stdout


def test_timeout_callback_applies_to_reads(monkeypatch) -> None:
    client = DummyClient()
    monkeypatch.setattr(cli, 'get_client', lambda: client)
    result = runner.invoke(cli.app, ['--timeout', '7', 'get_system_status'])
    assert result.exit_code == 0
    assert client.calls[-1] == ('get_system_status', (), {'timeout': 7.0})


def test_request_dry_run(monkeypatch) -> None:
    client = DummyClient()
    monkeypatch.setattr(cli, 'get_client', lambda: client)
    result = runner.invoke(cli.app, ['request', 'POST', '/api/profiles', '--param', 'verbose=true', '--body-json', '{"name":"demo"}', '--dry-run'])
    assert result.exit_code == 0
    assert '"method": "POST"' in result.stdout
    assert not client.calls


def test_create_profile_dry_run(monkeypatch) -> None:
    client = DummyClient()
    monkeypatch.setattr(cli, 'get_client', lambda: client)
    result = runner.invoke(cli.app, ['--timeout', '12', 'create_profile', 'demo', '--humanize', '--dry-run'])
    assert result.exit_code == 0
    assert '"path": "/api/profiles"' in result.stdout
    assert not client.calls
