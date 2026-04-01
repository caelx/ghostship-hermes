from __future__ import annotations

from typer.testing import CliRunner

from ghostship_romm import cli


runner = CliRunner()


class DummyClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple[object, ...], dict[str, object]]] = []

    def request(self, method: str, path: str, *, params=None, json_data=None):
        self.calls.append(("request", (method, path), {"params": params, "json_data": json_data}))
        return {"method": method, "path": path}

    def __getattr__(self, name: str):
        if name.startswith("get_") or name in {"update_rom", "delete_rom", "start_scan"}:
            def _method(*args, **kwargs):
                self.calls.append((name, args, kwargs))
                return {"name": name, "args": list(args), "kwargs": kwargs}
            return _method
        raise AttributeError(name)


def test_request(monkeypatch) -> None:
    client = DummyClient()
    monkeypatch.setattr(cli, "get_client", lambda: client)
    result = runner.invoke(cli.app, ["request", "GET", "platforms"])
    assert result.exit_code == 0


def test_canonical_commands(monkeypatch) -> None:
    client = DummyClient()
    monkeypatch.setattr(cli, "get_client", lambda: client)
    commands = [
        (["get_heartbeat"], "get_heartbeat", (), {}),
        (["get_platforms"], "get_platforms", (), {}),
        (["get_libraries"], "get_libraries", (), {}),
        (["get_roms", "--page", "2", "--page-size", "5", "--platform", "snes"], "get_roms", (), {"page": 2, "page_size": 5, "platform": "snes"}),
        (["get_rom", "3"], "get_rom", (3,), {}),
        (["update_rom", "3", "--body-json", '{"name":"Test"}'], "update_rom", (3, {"name": "Test"}), {}),
        (["delete_rom", "3"], "delete_rom", (3,), {}),
        (["get_scans"], "get_scans", (), {}),
        (["start_scan"], "start_scan", (None,), {}),
        (["start_scan", "--library-id", "4"], "start_scan", (4,), {}),
        (["get_collections"], "get_collections", (), {}),
        (["get_config"], "get_config", (), {}),
        (["get_saves", "--page", "2", "--page-size", "5"], "get_saves", (), {"page": 2, "page_size": 5}),
        (["get_saves_summary"], "get_saves_summary", (), {}),
        (["get_save", "6"], "get_save", (6,), {}),
        (["get_users"], "get_users", (), {}),
        (["get_user_me"], "get_user_me", (), {}),
    ]
    for argv, name, args, kwargs in commands:
        result = runner.invoke(cli.app, argv)
        assert result.exit_code == 0, result.stdout
        assert client.calls[-1] == (name, args, kwargs)
