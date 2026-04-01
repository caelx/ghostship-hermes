from __future__ import annotations

import json

from typer.testing import CliRunner

from ghostship_cli_contract import RequestSpec
from ghostship_bazarr import cli


runner = CliRunner()


class DummyClient:
    def __init__(self) -> None:
        self.default_timeout: float | None = None
        self.calls: list[tuple[str, tuple[object, ...], dict[str, object]]] = []

    def get_system_status(self, *, timeout=None):
        effective_timeout = self.default_timeout if timeout is None else timeout
        self.calls.append(("get_system_status", (), {"timeout": effective_timeout}))
        return {"status": "ok", "timeout": effective_timeout}

    def build_request(self, method: str, path: str, *, params=None, json_data=None, timeout=None):
        self.calls.append(("build_request", (method, path), {"params": params, "json_data": json_data, "timeout": timeout}))
        return RequestSpec(method=method, path=f"/{path}", params=params, json_body=json_data, timeout=timeout)


def test_get_system_status_uses_timeout(monkeypatch) -> None:
    client = DummyClient()
    monkeypatch.setattr(cli, "get_client", lambda: setattr(client, "default_timeout", cli.APP_STATE["timeout"]) or client)
    result = runner.invoke(cli.app, ["--timeout", "7", "get_system_status"])
    assert result.exit_code == 0
    assert json.loads(result.stdout) == {"status": "ok", "timeout": 7.0}


def test_request_dry_run(monkeypatch) -> None:
    client = DummyClient()
    monkeypatch.setattr(cli, "get_client", lambda: client)
    result = runner.invoke(cli.app, ["--timeout", "9", "request", "POST", "jobs", "--body-json", '{"x":1}', "--dry-run"])
    assert result.exit_code == 0
    assert json.loads(result.stdout) == {"method": "POST", "path": "/jobs", "json_body": {"x": 1}, "timeout": 9.0}


def test_search_subtitles_missing_dry_run(monkeypatch) -> None:
    client = DummyClient()
    monkeypatch.setattr(cli, "get_client", lambda: client)
    result = runner.invoke(cli.app, ["--timeout", "11", "search_subtitles_missing", "--dry-run"])
    assert result.exit_code == 0
    assert json.loads(result.stdout) == {"method": "POST", "path": "/subtitles/search/missing", "timeout": 11.0}
