from __future__ import annotations

from ghostship_prowlarr.client import ProwlarrClient


class DummyProwlarrClient(ProwlarrClient):
    def __init__(self) -> None:
        super().__init__("https://prowlarr.example", "token")
        self.calls: list[tuple[str, str, dict[str, object]]] = []

    def request(self, method: str, path: str, *, params=None, json_data=None, timeout=None):
        self.calls.append((method, path, {"params": params, "json_data": json_data, "timeout": timeout}))
        return {"ok": True}


def test_wrappers_delegate_to_request() -> None:
    client = DummyProwlarrClient()
    client.get_indexers(timeout=1.0)
    client.get_indexers(2, timeout=1.0)
    client.search("ubuntu", categories=[2000], timeout=1.0)
    client.get_applications(timeout=1.0)
    client.get_applications(3, timeout=1.0)
    client.get_history(page=2, page_size=5, timeout=1.0)
    client.get_status(timeout=1.0)
    client.run_command("SyncAppIndexers", timeout=1.0, applicationId=3)
    client.get_indexer_stats(timeout=1.0)
    client.get_indexer_status(timeout=1.0)

    assert client.calls == [
        ("GET", "indexer", {"params": None, "json_data": None, "timeout": 1.0}),
        ("GET", "indexer/2", {"params": None, "json_data": None, "timeout": 1.0}),
        ("GET", "search", {"params": {"query": "ubuntu", "categories": [2000]}, "json_data": None, "timeout": 1.0}),
        ("GET", "applications", {"params": None, "json_data": None, "timeout": 1.0}),
        ("GET", "applications/3", {"params": None, "json_data": None, "timeout": 1.0}),
        ("GET", "history", {"params": {"page": 2, "pageSize": 5}, "json_data": None, "timeout": 1.0}),
        ("GET", "system/status", {"params": None, "json_data": None, "timeout": 1.0}),
        ("POST", "command", {"params": None, "json_data": {"name": "SyncAppIndexers", "applicationId": 3}, "timeout": 1.0}),
        ("GET", "indexerstats", {"params": None, "json_data": None, "timeout": 1.0}),
        ("GET", "indexerstatus", {"params": None, "json_data": None, "timeout": 1.0}),
    ]


def test_build_request_prefixes_api_path() -> None:
    client = ProwlarrClient("https://prowlarr.example", "token")
    spec = client.build_request("POST", "command", json_data={"name": "SyncAppIndexers"}, timeout=8.0)
    assert spec.to_dict() == {"method": "POST", "path": "/api/v1/command", "timeout": 8.0, "json_body": {"name": "SyncAppIndexers"}, "headers": {"X-Api-Key": "token"}}
