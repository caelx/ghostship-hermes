from __future__ import annotations

from typer.testing import CliRunner

from ghostship_flaresolverr import cli


runner = CliRunner()


class DummyClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple[object, ...], dict[str, object]]] = []

    def command(self, cmd: str, **kwargs):
        self.calls.append(("command", (cmd,), kwargs))
        return {"cmd": cmd, "kwargs": kwargs}

    def __getattr__(self, name: str):
        if name in {"request_get", "request_post", "sessions_create", "sessions_list", "sessions_destroy"}:
            def _method(*args, **kwargs):
                self.calls.append((name, args, kwargs))
                return {"name": name, "args": list(args), "kwargs": kwargs}
            return _method
        raise AttributeError(name)


def test_command(monkeypatch) -> None:
    client = DummyClient()
    monkeypatch.setattr(cli, "get_client", lambda: client)
    result = runner.invoke(cli.app, ["command", "sessions.list"])
    assert result.exit_code == 0
    assert client.calls[-1] == ("command", ("sessions.list",), {})


def test_canonical_commands(monkeypatch) -> None:
    client = DummyClient()
    monkeypatch.setattr(cli, "get_client", lambda: client)
    commands = [
        (["request_get", "https://example.com", "--session", "a"], "request_get", ("https://example.com",), {"session": "a"}),
        (["request_post", "https://example.com", "body", "--session", "b"], "request_post", ("https://example.com", "body"), {"session": "b"}),
        (["sessions_create", "--session", "c"], "sessions_create", (), {"session": "c"}),
        (["sessions_list"], "sessions_list", (), {}),
        (["sessions_destroy", "d"], "sessions_destroy", ("d",), {}),
    ]
    for argv, name, args, kwargs in commands:
        result = runner.invoke(cli.app, argv)
        assert result.exit_code == 0, result.stdout
        assert client.calls[-1] == (name, args, kwargs)
