import json

from typer.testing import CliRunner

from ghostship_searxng.cli import app


runner = CliRunner()


def test_search_web_json_output(monkeypatch):
    def fake_search(
        *, base_url, query, categories, limit, language, safe_search, timeout
    ):
        assert base_url == "https://search.example"
        assert query == "nixos hermes"
        assert categories == "general"
        assert limit == 3
        assert language == "en"
        assert safe_search == 1
        assert timeout == 10.0
        return {
            "query": query,
            "number_of_results": 1,
            "results": [
                {
                    "title": "Ghostship Hermes",
                    "url": "https://example.com/ghostship-hermes",
                }
            ],
        }

    monkeypatch.setattr("ghostship_searxng.cli.search_searxng", fake_search)

    result = runner.invoke(
        app,
        [
            "search",
            "web",
            "nixos hermes",
            "--base-url",
            "https://search.example",
            "--category",
            "general",
            "--limit",
            "3",
            "--language",
            "en",
            "--safe-search",
            "1",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["query"] == "nixos hermes"
    assert payload["number_of_results"] == 1
    assert payload["results"][0]["title"] == "Ghostship Hermes"


def test_search_web_human_output(monkeypatch):
    def fake_search(
        *, base_url, query, categories, limit, language, safe_search, timeout
    ):
        return {
            "query": query,
            "number_of_results": 2,
            "results": [
                {
                    "title": "Ghostship Hermes",
                    "url": "https://example.com/ghostship-hermes",
                },
                {
                    "title": "Hermes Agent",
                    "url": "https://example.com/hermes",
                },
            ],
        }

    monkeypatch.setattr("ghostship_searxng.cli.search_searxng", fake_search)

    result = runner.invoke(app, ["search", "web", "hermes"])

    assert result.exit_code == 0
    assert "Ghostship Hermes" in result.stdout
    assert "https://example.com/hermes" in result.stdout
