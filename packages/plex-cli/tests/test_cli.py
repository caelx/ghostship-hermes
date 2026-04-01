from __future__ import annotations

from typer.testing import CliRunner

from ghostship_plex import cli


runner = CliRunner()


class DummyClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple[object, ...], dict[str, object]]] = []

    def request(self, method: str, path: str, *, params=None, json_data=None):
        self.calls.append(("request", (method, path), {"params": params, "json_data": json_data}))
        return {"method": method, "path": path}

    def __getattr__(self, name: str):
        if name.startswith("get_") or name in {"refresh_library", "terminate_session"}:
            def _method(*args, **kwargs):
                self.calls.append((name, args, kwargs))
                return {"name": name, "args": list(args), "kwargs": kwargs}
            return _method
        raise AttributeError(name)


def test_request(monkeypatch) -> None:
    client = DummyClient()
    monkeypatch.setattr(cli, "get_client", lambda: client)
    result = runner.invoke(cli.app, ["request", "GET", "identity"])
    assert result.exit_code == 0
    assert client.calls[-1] == ("request", ("GET", "identity"), {"params": None, "json_data": None})


def test_canonical_commands(monkeypatch) -> None:
    client = DummyClient()
    monkeypatch.setattr(cli, "get_client", lambda: client)
    commands = [
        (["get_identity"], "get_identity", (), {}),
        (["get_server_info"], "get_server_info", (), {}),
        (["get_status_sessions"], "get_status_sessions", (), {}),
        (["get_activities"], "get_activities", (), {}),
        (["get_library_sections"], "get_library_sections", (), {}),
        (["get_library_section", "1"], "get_library_section", (1,), {}),
        (["get_library_filters", "1"], "get_library_filters", (1,), {}),
        (["get_library_sorts", "1"], "get_library_sorts", (1,), {}),
        (["refresh_library"], "refresh_library", (None,), {}),
        (["refresh_library", "--section-id", "1"], "refresh_library", (1,), {}),
        (["get_metadata", "3"], "get_metadata", (3,), {}),
        (["get_metadata_children", "3"], "get_metadata_children", (3,), {}),
        (["get_playlists"], "get_playlists", (), {}),
        (["get_playlist_items", "4"], "get_playlist_items", (4,), {}),
        (["get_collections", "1"], "get_collections", (1,), {}),
        (["get_preferences"], "get_preferences", (), {}),
        (["get_butler_tasks"], "get_butler_tasks", (), {}),
        (["get_statistics"], "get_statistics", (), {}),
        (["terminate_session", "7"], "terminate_session", (7,), {}),
        (["get_session", "7"], "get_session", (7,), {}),
    ]
    for argv, name, args, kwargs in commands:
        result = runner.invoke(cli.app, argv)
        assert result.exit_code == 0, result.stdout
        assert client.calls[-1] == (name, args, kwargs)
