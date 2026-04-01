from __future__ import annotations

from typer.testing import CliRunner

from ghostship_searxng import cli


runner = CliRunner()


def test_search_web(monkeypatch) -> None:
    monkeypatch.setattr(cli, "search_searxng", lambda **kwargs: {"query": kwargs["query"], "results": []})
    result = runner.invoke(cli.app, ["search", "web", "ghostship hermes"])
    assert result.exit_code == 0
    assert '"query": "ghostship hermes"' in result.stdout


def test_request(monkeypatch) -> None:
    monkeypatch.setattr(cli, "request_searxng", lambda **kwargs: {"path": kwargs["path"], "params": kwargs["params"]})
    result = runner.invoke(cli.app, ["request", "search", "--param", "q=test"])
    assert result.exit_code == 0
    assert '"path": "search"' in result.stdout
