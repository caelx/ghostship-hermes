from __future__ import annotations

from typer.testing import CliRunner

from ghostship_flaresolverr import cli


runner = CliRunner()


class DummyClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple[object, ...], dict[str, object]]] = []

    def build_command(self, cmd: str, **kwargs):
        class _Spec:
            def __init__(self, payload):
                self.payload = payload
            def to_dict(self):
                return self.payload
        return _Spec({'method': 'POST', 'path': '/v1', 'json_body': {'cmd': cmd, **kwargs}, 'timeout': 30})

    def build_request_post(self, url: str, post_data: str, session: str | None = None):
        return self.build_command('request.post', url=url, postData=post_data, session=session)

    def build_sessions_create(self, session: str | None = None):
        return self.build_command('sessions.create', session=session)

    def build_sessions_destroy(self, session: str):
        return self.build_command('sessions.destroy', session=session)

    def command(self, cmd: str, timeout: float | None = None, **kwargs):
        self.calls.append(('command', (cmd,), {'timeout': timeout, **kwargs}))
        return {'cmd': cmd, 'kwargs': kwargs}

    def request_get(self, url: str, session: str | None = None, timeout: float | None = None):
        self.calls.append(('request_get', (url,), {'session': session, 'timeout': timeout}))
        return {'ok': True}

    def request_post(self, url: str, post_data: str, session: str | None = None, timeout: float | None = None):
        self.calls.append(('request_post', (url, post_data), {'session': session, 'timeout': timeout}))
        return {'ok': True}

    def sessions_create(self, session: str | None = None, timeout: float | None = None):
        self.calls.append(('sessions_create', (), {'session': session, 'timeout': timeout}))
        return {'ok': True}

    def sessions_list(self, timeout: float | None = None):
        self.calls.append(('sessions_list', (), {'timeout': timeout}))
        return {'ok': True}

    def sessions_destroy(self, session: str, timeout: float | None = None):
        self.calls.append(('sessions_destroy', (session,), {'timeout': timeout}))
        return {'ok': True}


def test_command_dry_run(monkeypatch) -> None:
    client = DummyClient()
    monkeypatch.setattr(cli, 'get_client', lambda: client)
    result = runner.invoke(cli.app, ['command', 'sessions.list', '--dry-run'])
    assert result.exit_code == 0
    assert '"cmd": "sessions.list"' in result.stdout
    assert not client.calls


def test_timeout_callback_applies(monkeypatch) -> None:
    client = DummyClient()
    monkeypatch.setattr(cli, 'get_client', lambda: client)
    result = runner.invoke(cli.app, ['--timeout', '9', 'sessions_list'])
    assert result.exit_code == 0
    assert client.calls[-1] == ('sessions_list', (), {'timeout': 9.0})


def test_canonical_commands(monkeypatch) -> None:
    client = DummyClient()
    monkeypatch.setattr(cli, 'get_client', lambda: client)
    commands = [
        (['request_get', 'https://example.com', '--session', 'a'], ('request_get', ('https://example.com',), {'session': 'a', 'timeout': 30.0})),
        (['request_post', 'https://example.com', 'body', '--session', 'b'], ('request_post', ('https://example.com', 'body'), {'session': 'b', 'timeout': 30.0})),
        (['sessions_create', '--session', 'c'], ('sessions_create', (), {'session': 'c', 'timeout': 30.0})),
        (['sessions_list'], ('sessions_list', (), {'timeout': 30.0})),
        (['sessions_destroy', 'd'], ('sessions_destroy', ('d',), {'timeout': 30.0})),
    ]
    for argv, expected in commands:
        result = runner.invoke(cli.app, argv)
        assert result.exit_code == 0, result.stdout
        assert client.calls[-1] == expected
