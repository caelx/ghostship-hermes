from __future__ import annotations

from typer.testing import CliRunner

from ghostship_bazarr import cli


runner = CliRunner()


class DummyClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple[object, ...], dict[str, object]]] = []

    def request(self, method: str, path: str, *, params=None, json_data=None):
        self.calls.append(("request", (method, path), {"params": params, "json_data": json_data}))
        return {"method": method, "path": path, "params": params, "json_data": json_data}

    def __getattr__(self, name: str):
        if name.startswith("get_") or name == "search_subtitles_missing":
            def _method(*args, **kwargs):
                self.calls.append((name, args, kwargs))
                return {"name": name, "args": list(args), "kwargs": kwargs}
            return _method
        raise AttributeError(name)


def test_request(monkeypatch) -> None:
    client = DummyClient()
    monkeypatch.setattr(cli, "get_client", lambda: client)
    result = runner.invoke(cli.app, ["request", "GET", "badges", "--param", "page=1"])
    assert result.exit_code == 0
    assert client.calls[-1] == ("request", ("GET", "badges"), {"params": {"page": "1"}, "json_data": None})


def test_canonical_commands(monkeypatch) -> None:
    client = DummyClient()
    monkeypatch.setattr(cli, "get_client", lambda: client)
    commands = [
        (["get_badges"], "get_badges", (), {}),
        (["get_episodes", "--series-id", "4"], "get_episodes", (), {"series_id": 4}),
        (["get_wanted_episodes"], "get_wanted_episodes", (), {}),
        (["get_movies"], "get_movies", (), {}),
        (["get_wanted_movies"], "get_wanted_movies", (), {}),
        (["get_series"], "get_series", (), {}),
        (["get_providers"], "get_providers", (), {}),
        (["get_subtitles"], "get_subtitles", (), {}),
        (["get_system_health"], "get_system_health", (), {}),
        (["get_system_jobs"], "get_system_jobs", (), {}),
        (["get_system_tasks"], "get_system_tasks", (), {}),
        (["get_system_status"], "get_system_status", (), {}),
        (["search_subtitles_missing"], "search_subtitles_missing", (), {}),
        (["get_episodes_history"], "get_episodes_history", (), {}),
        (["get_movies_history"], "get_movies_history", (), {}),
        (["get_episodes_blacklist"], "get_episodes_blacklist", (), {}),
        (["get_movies_blacklist"], "get_movies_blacklist", (), {}),
    ]
    for argv, name, args, kwargs in commands:
        result = runner.invoke(cli.app, argv)
        assert result.exit_code == 0, result.stdout
        assert client.calls[-1] == (name, args, kwargs)
