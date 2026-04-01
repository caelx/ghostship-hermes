from __future__ import annotations

from ghostship_prowlarr.client import ProwlarrClient


class DummyProwlarrClient(ProwlarrClient):
    def __init__(self) -> None:
        super().__init__("https://prowlarr.example", "token")
        self.calls: list[tuple[str, str, dict[str, object]]] = []

    def request(self, method: str, path: str, *, params=None, json_data=None):
        self.calls.append((method, path, {"params": params, "json_data": json_data}))
        return {"ok": True}


def test_wrappers_delegate_to_request() -> None:
    client = DummyProwlarrClient()
    client.get_indexers()
    client.get_indexers(4)
    client.search("ubuntu", categories=[2000])
    client.get_applications()
    client.get_applications(5)
    client.get_history(page=3, page_size=4)
    client.get_status()
    client.run_command("ApplicationSync")
    client.get_indexer_stats()
    client.get_indexer_status()

    assert client.calls == [
        ("GET", "indexer", {"params": None, "json_data": None}),
        ("GET", "indexer/4", {"params": None, "json_data": None}),
        ("GET", "search", {"params": {"query": "ubuntu", "categories": [2000]}, "json_data": None}),
        ("GET", "applications", {"params": None, "json_data": None}),
        ("GET", "applications/5", {"params": None, "json_data": None}),
        ("GET", "history", {"params": {"page": 3, "pageSize": 4}, "json_data": None}),
        ("GET", "system/status", {"params": None, "json_data": None}),
        ("POST", "command", {"params": None, "json_data": {"name": "ApplicationSync"}}),
        ("GET", "indexerstats", {"params": None, "json_data": None}),
        ("GET", "indexerstatus", {"params": None, "json_data": None}),
    ]
