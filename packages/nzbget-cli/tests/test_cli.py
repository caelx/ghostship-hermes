from __future__ import annotations

from typer.testing import CliRunner

from ghostship_nzbget import cli


runner = CliRunner()


class DummyClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple[object, ...], dict[str, object]]] = []

    def get_status(self):
        self.calls.append(("get_status", (), {}))
        return {"status": "ok"}

    def call(self, method: str, params=None):
        self.calls.append(("call", (method,), {"params": params}))
        return {"method": method, "params": params}


def test_get_status(monkeypatch) -> None:
    client = DummyClient()
    monkeypatch.setattr(cli, "get_client", lambda: client)
    result = runner.invoke(cli.app, ["get_status"])
    assert result.exit_code == 0


def test_call(monkeypatch) -> None:
    client = DummyClient()
    monkeypatch.setattr(cli, "get_client", lambda: client)
    result = runner.invoke(cli.app, ["call", "config", "--params-json", '[1,2]'])
    assert result.exit_code == 0
    assert client.calls[-1] == ("call", ("config",), {"params": [1, 2]})
