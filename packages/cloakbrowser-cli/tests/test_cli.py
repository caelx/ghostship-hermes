from __future__ import annotations

from typer.testing import CliRunner

from ghostship_cloakbrowser import cli


runner = CliRunner()


class DummyClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple[object, ...], dict[str, object]]] = []

    def get_system_status(self):
        self.calls.append(("get_system_status", (), {}))
        return {"status": "ok"}

    def request(self, method: str, path: str, *, params=None, json_data=None):
        self.calls.append(("request", (method, path), {"params": params, "json_data": json_data}))
        return {"method": method, "path": path}


def test_root_help_explains_static_token_auth() -> None:
    result = runner.invoke(cli.app, ["--help"])
    assert result.exit_code == 0
    assert "CLOAKBROWSER_URL" in result.stdout
    assert "CLOAKBROWSER_TOKEN" in result.stdout
    assert "AUTH_TOKEN" in result.stdout


def test_status(monkeypatch) -> None:
    client = DummyClient()
    monkeypatch.setattr(cli, "get_client", lambda: client)
    result = runner.invoke(cli.app, ["get_system_status"])
    assert result.exit_code == 0


def test_request(monkeypatch) -> None:
    client = DummyClient()
    monkeypatch.setattr(cli, "get_client", lambda: client)
    result = runner.invoke(cli.app, ["request", "POST", "/api/profiles", "--param", "verbose=true", "--body-json", '{"name":"demo"}'])
    assert result.exit_code == 0
    assert client.calls[-1] == ("request", ("POST", "/api/profiles"), {"params": {"verbose": "true"}, "json_data": {"name": "demo"}})
