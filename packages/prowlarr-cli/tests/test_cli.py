from __future__ import annotations

from typer.testing import CliRunner

from ghostship_prowlarr import cli


runner = CliRunner()


class DummyClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple[object, ...], dict[str, object]]] = []

    def get_status(self) -> dict[str, str]:
        self.calls.append(("get_status", (), {}))
        return {"version": "1.0.0"}

    def request(self, method: str, path: str, *, params=None, json_data=None):
        self.calls.append(("request", (method, path), {"params": params, "json_data": json_data}))
        return {"method": method, "path": path, "params": params, "json_data": json_data}


def test_info(monkeypatch) -> None:
    client = DummyClient()
    monkeypatch.setattr(cli, "get_client", lambda: client)
    result = runner.invoke(cli.app, ["get_status"])
    assert result.exit_code == 0
    assert result.stdout.strip() == '{"version": "1.0.0"}'
    assert client.calls == [("get_status", (), {})]


def test_request(monkeypatch) -> None:
    client = DummyClient()
    monkeypatch.setattr(cli, "get_client", lambda: client)
    result = runner.invoke(
        cli.app,
        ["request", "GET", "indexer", "--param", "page=1"],
    )
    assert result.exit_code == 0
    assert '"path": "indexer"' in result.stdout
    assert client.calls == [
        ("request", ("GET", "indexer"), {"params": {"page": "1"}, "json_data": None})
    ]
