from __future__ import annotations

from typer.testing import CliRunner

from ghostship_tautulli import cli


runner = CliRunner()


class DummyClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple[object, ...], dict[str, object]]] = []

    def call(self, cmd: str, **kwargs):
        self.calls.append(("call", (cmd,), kwargs))
        return {"cmd": cmd, "kwargs": kwargs}

    def __getattr__(self, name: str):
        if name.startswith("get_") or name in {"terminate_session", "search", "restart"}:
            def _method(*args, **kwargs):
                self.calls.append((name, args, kwargs))
                return {"name": name, "args": list(args), "kwargs": kwargs}
            return _method
        raise AttributeError(name)


def test_call(monkeypatch) -> None:
    client = DummyClient()
    monkeypatch.setattr(cli, "get_client", lambda: client)
    result = runner.invoke(cli.app, ["call", "get_users", "--param", "limit=5"])
    assert result.exit_code == 0
    assert client.calls[-1] == ("call", ("get_users",), {"limit": "5"})


def test_canonical_commands(monkeypatch) -> None:
    client = DummyClient()
    monkeypatch.setattr(cli, "get_client", lambda: client)
    commands = [
        (["get_server_status"], "get_server_status", (), {}),
        (["get_tautulli_info"], "get_tautulli_info", (), {}),
        (["get_status"], "get_status", (), {}),
        (["get_activity"], "get_activity", (), {}),
        (["terminate_session", "abc", "--message", "bye"], "terminate_session", ("abc",), {"message": "bye"}),
        (["get_history", "--page", "2", "--length", "5", "--search", "office"], "get_history", (), {"page": 2, "length": 5, "search": "office", "order_column": "date", "order_dir": "desc"}),
        (["get_libraries"], "get_libraries", (), {}),
        (["get_library_user_stats", "4"], "get_library_user_stats", (4,), {}),
        (["get_users"], "get_users", (), {}),
        (["get_user_player_stats", "7"], "get_user_player_stats", (7,), {}),
        (["get_user_watch_time_stats", "7"], "get_user_watch_time_stats", (7,), {}),
        (["get_metadata", "9"], "get_metadata", (9,), {}),
        (["search", "office", "--limit", "3"], "search", ("office",), {"limit": 3}),
        (["restart"], "restart", (), {}),
    ]
    for argv, name, args, kwargs in commands:
        result = runner.invoke(cli.app, argv)
        assert result.exit_code == 0, result.stdout
        assert client.calls[-1] == (name, args, kwargs)
