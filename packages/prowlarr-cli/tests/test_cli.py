from __future__ import annotations

import json

from typer.testing import CliRunner

from ghostship_cli_contract import RequestSpec
from ghostship_prowlarr import cli


runner = CliRunner()


class DummyClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple[object, ...], dict[str, object]]] = []
        self.default_timeout: float | None = None

    def get_status(self, *, timeout=None) -> dict[str, object]:
        effective_timeout = self.default_timeout if timeout is None else timeout
        self.calls.append(("get_status", (), {"timeout": effective_timeout}))
        return {"version": "1.0.0", "timeout": effective_timeout}

    def build_request(self, method: str, path: str, *, params=None, json_data=None, timeout=None):
        self.calls.append(("build_request", (method, path), {"params": params, "json_data": json_data, "timeout": timeout}))
        return RequestSpec(method=method, path=f"/api/v1/{path}", params=params, json_body=json_data, timeout=timeout)


def test_get_status_uses_timeout(monkeypatch) -> None:
    client = DummyClient()
    monkeypatch.setattr(cli, "get_client", lambda: setattr(client, "default_timeout", cli.APP_STATE["timeout"]) or client)
    result = runner.invoke(cli.app, ["--timeout", "7", "get_status"])
    assert result.exit_code == 0
    assert json.loads(result.stdout) == {"version": "1.0.0", "timeout": 7.0}


def test_request_dry_run_prints_request_spec(monkeypatch) -> None:
    client = DummyClient()
    monkeypatch.setattr(cli, "get_client", lambda: client)
    result = runner.invoke(cli.app, ["--timeout", "9", "request", "POST", "command", "--body-json", '{"name":"SyncAppIndexers"}', "--dry-run"])
    assert result.exit_code == 0
    assert json.loads(result.stdout) == {"method": "POST", "path": "/api/v1/command", "json_body": {"name": "SyncAppIndexers"}, "timeout": 9.0}


def test_run_command_dry_run_uses_request_builder(monkeypatch) -> None:
    client = DummyClient()
    monkeypatch.setattr(cli, "get_client", lambda: client)
    result = runner.invoke(cli.app, ["--timeout", "11", "run_command", "SyncAppIndexers", "--args", '{"applicationId":1}', "--dry-run"])
    assert result.exit_code == 0
    assert json.loads(result.stdout) == {"method": "POST", "path": "/api/v1/command", "json_body": {"name": "SyncAppIndexers", "applicationId": 1}, "timeout": 11.0}
