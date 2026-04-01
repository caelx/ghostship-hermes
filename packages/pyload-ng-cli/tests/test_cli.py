from __future__ import annotations

from typer.testing import CliRunner

from ghostship_pyload_ng import cli


runner = CliRunner()


class DummyClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple[object, ...], dict[str, object]]] = []

    def get_server_status(self):
        self.calls.append(("get_server_status", (), {}))
        return {"status": "ok"}

    def request(self, method: str, path: str, *, params=None, json_data=None):
        self.calls.append(("request", (method, path), {"params": params, "json_data": json_data}))
        return {"method": method, "path": path, "params": params, "json_data": json_data}


def test_get_server_status(monkeypatch) -> None:
    client = DummyClient()
    monkeypatch.setattr(cli, "get_client", lambda: client)
    result = runner.invoke(cli.app, ["get_server_status"])
    assert result.exit_code == 0


def test_request(monkeypatch) -> None:
    client = DummyClient()
    monkeypatch.setattr(cli, "get_client", lambda: client)
    result = runner.invoke(cli.app, ["request", "POST", "api/toggle_pause"])
    assert result.exit_code == 0
    assert client.calls[-1] == ("request", ("POST", "api/toggle_pause"), {"params": None, "json_data": None})
