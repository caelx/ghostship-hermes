from __future__ import annotations

from typer.testing import CliRunner

from ghostship_synology import cli


runner = CliRunner()


class DummyClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple[object, ...], dict[str, object]]] = []
        self.sid = 'sid-1'

    def logout(self):
        self.calls.append(("logout", (), {}))
        return True

    def call(self, api: str, method: str, *, version=None, path=None, params=None, http_method=None):
        self.calls.append(("call", (api, method), {"version": version, "path": path, "params": params, "http_method": http_method}))
        return {"ok": True}

    def __getattr__(self, name: str):
        if name in {"get_info", "login", "list_shares", "list_files", "get_file_info", "search_start", "search_list", "create_folder", "rename", "delete", "download_file", "upload_file", "copy", "move"}:
            def _method(*args, **kwargs):
                self.calls.append((name, args, kwargs))
                if name == 'download_file':
                    class Response:
                        content = b'data'
                    return Response()
                if name == 'search_start':
                    return 'task-1'
                if name == 'delete':
                    return 'task-2'
                return {"name": name, "args": list(args), "kwargs": kwargs}
            return _method
        raise AttributeError(name)


def test_call(monkeypatch) -> None:
    client = DummyClient()
    monkeypatch.setattr(cli, "get_client", lambda: client)
    result = runner.invoke(cli.app, ["call", "SYNO.FileStation.List", "list", "--param-json", '{"folder_path":"/music"}', "--http-method", "POST"])
    assert result.exit_code == 0
    assert client.calls[0] == ("call", ("SYNO.FileStation.List", "list"), {"version": None, "path": None, "params": {"folder_path": "/music"}, "http_method": "POST"})


def test_canonical_commands(monkeypatch, tmp_path) -> None:
    client = DummyClient()
    monkeypatch.setattr(cli, "get_client", lambda: client)
    output = tmp_path / 'song.mp3'
    commands = [
        (["get_info"], "get_info", (), {"query": "all"}),
        (["list_shares"], "list_shares", (), {}),
        (["list_files", "/music", "--offset", "10", "--limit", "20", "--sort-by", "size"], "list_files", ("/music",), {"offset": 10, "limit": 20, "sort_by": "size"}),
        (["get_file_info", "/music/song.mp3"], "get_file_info", ("/music/song.mp3",), {}),
        (["search_start", "/music", "song"], "search_start", ("/music", "song"), {"recursive": True}),
        (["search_list", "task-1", "--offset", "5", "--limit", "6"], "search_list", ("task-1",), {"offset": 5, "limit": 6}),
        (["create_folder", "/music", "new"], "create_folder", ("/music", "new"), {"force_parent": False}),
        (["rename", "/music/old", "new"], "rename", ("/music/old", "new"), {}),
        (["delete", "/music/old"], "delete", ("/music/old",), {"recursive": True}),
        (["upload_file", "/music", __file__], "upload_file", ("/music", __file__), {"create_parents": True}),
        (["copy", "/music/a", "/music/b", "--no-overwrite"], "copy", ("/music/a", "/music/b"), {"overwrite": False}),
        (["move", "/music/a", "/music/b"], "move", ("/music/a", "/music/b"), {"overwrite": True}),
    ]
    for argv, name, args, kwargs in commands:
        result = runner.invoke(cli.app, argv)
        assert result.exit_code == 0, result.stdout
        assert client.calls[-2] == (name, args, kwargs)
        assert client.calls[-1] == ("logout", (), {})
    result = runner.invoke(cli.app, ["download_file", "/music/song.mp3", "--output", str(output)])
    assert result.exit_code == 0, result.stdout
    assert output.read_bytes() == b'data'
