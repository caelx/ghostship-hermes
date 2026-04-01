from __future__ import annotations

from ghostship_synology.client import SynologyClient


class DummySynologyClient(SynologyClient):
    def __init__(self) -> None:
        super().__init__("https://synology.example", "user", "pass")
        self.calls: list[tuple[str, str, dict[str, object]]] = []

    def call(self, api: str, method: str, *, version=None, path=None, params=None, http_method=None, files=None, use_sid=True):
        self.calls.append((api, method, {"version": version, "path": path, "params": params, "http_method": http_method, "files": files, "use_sid": use_sid}))
        if api == "SYNO.FileStation.Search" and method == "start":
            return {"taskid": "task-1"}
        if api == "SYNO.FileStation.Delete" and method == "start":
            return {"taskid": "task-2"}
        if api == "SYNO.API.Info":
            return {"SYNO.API.Auth": {"maxVersion": 6, "path": "auth.cgi"}}
        if api == "SYNO.API.Auth" and method == "login":
            return {"sid": "sid-1"}
        return {"ok": True}


def test_wrappers_delegate_to_call() -> None:
    client = DummySynologyClient()
    client.get_info()
    client.login()
    client.logout()
    client.list_shares()
    client.list_files("/music", offset=10, limit=20, sort_by="size")
    client.get_file_info("/music/song.mp3")
    client.search_start("/music", "song")
    client.search_list("task-1", offset=5, limit=6)
    client.create_folder("/music", "new")
    client.rename("/music/old", "new")
    client.delete("/music/old")
    client.copy("/music/a", "/music/b", overwrite=False)
    client.move("/music/a", "/music/b")

    assert client.calls == [
        ("SYNO.API.Info", "query", {"version": 1, "path": "query.cgi", "params": {"query": "all"}, "http_method": None, "files": None, "use_sid": False}),
        ("SYNO.API.Auth", "login", {"version": 6, "path": "auth.cgi", "params": {"account": "user", "passwd": "pass", "session": "FileStation", "format": "sid"}, "http_method": None, "files": None, "use_sid": False}),
        ("SYNO.API.Auth", "logout", {"version": 6, "path": "auth.cgi", "params": {"session": "FileStation"}, "http_method": None, "files": None, "use_sid": False}),
        ("SYNO.FileStation.List", "list_share", {"version": None, "path": None, "params": None, "http_method": None, "files": None, "use_sid": True}),
        ("SYNO.FileStation.List", "list", {"version": None, "path": None, "params": {"folder_path": "/music", "offset": 10, "limit": 20, "sort_by": "size"}, "http_method": None, "files": None, "use_sid": True}),
        ("SYNO.FileStation.List", "getinfo", {"version": None, "path": None, "params": {"path": "/music/song.mp3"}, "http_method": None, "files": None, "use_sid": True}),
        ("SYNO.FileStation.Search", "start", {"version": None, "path": None, "params": {"folder_path": "/music", "pattern": "song", "recursive": "true"}, "http_method": None, "files": None, "use_sid": True}),
        ("SYNO.FileStation.Search", "list", {"version": None, "path": None, "params": {"taskid": "task-1", "offset": 5, "limit": 6}, "http_method": None, "files": None, "use_sid": True}),
        ("SYNO.FileStation.CreateFolder", "create", {"version": None, "path": None, "params": {"folder_path": "/music", "name": "new", "force_parent": "false"}, "http_method": None, "files": None, "use_sid": True}),
        ("SYNO.FileStation.Rename", "rename", {"version": None, "path": None, "params": {"path": "/music/old", "name": "new"}, "http_method": None, "files": None, "use_sid": True}),
        ("SYNO.FileStation.Delete", "start", {"version": None, "path": None, "params": {"path": "/music/old", "recursive": "true"}, "http_method": None, "files": None, "use_sid": True}),
        ("SYNO.FileStation.CopyMove", "copy", {"version": None, "path": None, "params": {"path": "/music/a", "destination": "/music/b", "overwrite": "false"}, "http_method": "POST", "files": None, "use_sid": True}),
        ("SYNO.FileStation.CopyMove", "move", {"version": None, "path": None, "params": {"path": "/music/a", "destination": "/music/b", "overwrite": "true"}, "http_method": "POST", "files": None, "use_sid": True}),
    ]
