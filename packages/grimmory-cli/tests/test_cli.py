from __future__ import annotations

from typer.testing import CliRunner

from ghostship_grimmory import cli


runner = CliRunner()


class DummyClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple[object, ...], dict[str, object]]] = []

    def request(self, method: str, path: str, *, params=None, json_data=None):
        self.calls.append(("request", (method, path), {"params": params, "json_data": json_data}))
        return {"method": method, "path": path}

    def __getattr__(self, name: str):
        if name.startswith("get_") or name in {"download_book", "scan_libraries", "refresh_library", "cancel_task"}:
            def _method(*args, **kwargs):
                self.calls.append((name, args, kwargs))
                return {"name": name, "args": list(args), "kwargs": kwargs}
            return _method
        raise AttributeError(name)


def test_request(monkeypatch) -> None:
    client = DummyClient()
    monkeypatch.setattr(cli, "get_client", lambda: client)
    result = runner.invoke(cli.app, ["request", "GET", "books", "--param", "page=1"])
    assert result.exit_code == 0


def test_canonical_commands(monkeypatch) -> None:
    client = DummyClient()
    monkeypatch.setattr(cli, "get_client", lambda: client)
    commands = [
        (["get_books", "--page", "1", "--size", "5", "--library-id", "2"], "get_books", (), {"page": 1, "size": 5, "library_id": 2}),
        (["get_book", "3"], "get_book", (3,), {}),
        (["download_book", "3"], "download_book", (3,), {}),
        (["get_libraries"], "get_libraries", (), {}),
        (["get_library", "1"], "get_library", (1,), {}),
        (["scan_libraries"], "scan_libraries", (), {}),
        (["refresh_library", "1"], "refresh_library", (1,), {}),
        (["get_authors", "--page", "1", "--size", "5"], "get_authors", (), {"page": 1, "size": 5}),
        (["get_author", "2"], "get_author", (2,), {}),
        (["get_shelves"], "get_shelves", (), {}),
        (["get_shelf_books", "4"], "get_shelf_books", (4,), {}),
        (["get_tasks"], "get_tasks", (), {}),
        (["cancel_task", "abc"], "cancel_task", ("abc",), {}),
        (["get_version"], "get_version", (), {}),
    ]
    for argv, name, args, kwargs in commands:
        result = runner.invoke(cli.app, argv)
        assert result.exit_code == 0, result.stdout
        assert client.calls[-1] == (name, args, kwargs)
