from __future__ import annotations

from typer.testing import CliRunner

from ghostship_qbittorrent import cli


runner = CliRunner()


class DummyClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple[object, ...], dict[str, object]]] = []

    def get_transfer_info(self):
        self.calls.append(("get_transfer_info", (), {}))
        return {"status": "ok"}

    def request(self, method: str, path: str, *, params=None, data=None, json_data=None, files=None):
        self.calls.append(("request", (method, path), {"params": params, "data": data, "json_data": json_data, "files": files}))
        return {"method": method, "path": path}


def test_get_transfer_info(monkeypatch) -> None:
    client = DummyClient()
    monkeypatch.setattr(cli, "get_client", lambda: client)
    result = runner.invoke(cli.app, ["get_transfer_info"])
    assert result.exit_code == 0


def test_request(monkeypatch) -> None:
    client = DummyClient()
    monkeypatch.setattr(cli, "get_client", lambda: client)
    result = runner.invoke(cli.app, ["request", "POST", "torrents/pause", "--data", "hashes=abc"])
    assert result.exit_code == 0
    assert client.calls[-1] == ("request", ("POST", "torrents/pause"), {"params": None, "data": {"hashes": "abc"}, "json_data": None, "files": None})
