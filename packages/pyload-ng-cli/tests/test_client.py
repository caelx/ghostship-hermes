from __future__ import annotations

from ghostship_pyload_ng.client import PyLoadClient


class DummyPyLoadClient(PyLoadClient):
    def __init__(self) -> None:
        super().__init__("https://pyload.example")
        self.calls: list[tuple[str, str, dict[str, object]]] = []

    def request(self, method: str, path: str, *, params=None, json_data=None):
        self.calls.append((method, path, {"params": params, "json_data": json_data}))
        return {"ok": True}


def test_wrappers_delegate_to_request() -> None:
    client = DummyPyLoadClient()
    client.get_server_status()
    client.get_downloads()
    client.get_queue()
    client.add_package("pkg", ["http://example.com"])
    client.add_files(4, ["http://example.com/2"])
    client.delete_packages([1, 2])
    client.toggle_pause()
    client.get_config()
    client.delete_finished()
    client.restart_failed()
    client.stop_all_downloads()
    client.get_accounts(refresh=True)
    client.add_account("plugin", "user", "pass")
    client.remove_account("plugin", "user")
    client.get_server_version()
    client.get_free_space()

    assert client.calls == [
        ("GET", "api/status_server", {"params": None, "json_data": None}),
        ("GET", "api/status_downloads", {"params": None, "json_data": None}),
        ("GET", "api/get_queue", {"params": None, "json_data": None}),
        ("POST", "api/add_package", {"params": None, "json_data": {"name": "pkg", "links": ["http://example.com"]}}),
        ("POST", "api/add_files", {"params": None, "json_data": {"package_id": 4, "links": ["http://example.com/2"]}}),
        ("POST", "api/delete_packages", {"params": None, "json_data": {"package_ids": [1, 2]}}),
        ("POST", "api/toggle_pause", {"params": None, "json_data": None}),
        ("GET", "api/get_config_dict", {"params": None, "json_data": None}),
        ("POST", "api/delete_finished", {"params": None, "json_data": None}),
        ("POST", "api/restart_failed", {"params": None, "json_data": None}),
        ("POST", "api/stop_all_downloads", {"params": None, "json_data": None}),
        ("GET", "api/get_accounts", {"params": {"refresh": "true"}, "json_data": None}),
        ("POST", "api/update_account", {"params": None, "json_data": {"plugin": "plugin", "login": "user", "password": "pass"}}),
        ("POST", "api/remove_account", {"params": None, "json_data": {"plugin": "plugin", "login": "user"}}),
        ("GET", "api/get_server_version", {"params": None, "json_data": None}),
        ("GET", "api/free_space", {"params": None, "json_data": None}),
    ]
