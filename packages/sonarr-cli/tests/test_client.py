from __future__ import annotations

from ghostship_sonarr.client import SonarrClient


class DummySonarrClient(SonarrClient):
    def __init__(self) -> None:
        super().__init__("https://sonarr.example", "token")
        self.calls: list[tuple[str, str, dict[str, object]]] = []

    def request(self, method: str, path: str, *, params=None, json_data=None, timeout=None):
        self.calls.append((method, path, {"params": params, "json_data": json_data, "timeout": timeout}))
        return {"ok": True}


def test_wrappers_delegate_to_request() -> None:
    client = DummySonarrClient()
    client.get_series(timeout=1.0)
    client.get_series(2, timeout=1.0)
    client.lookup_series("office", timeout=1.0)
    client.add_series({"title": "Office"}, timeout=1.0)
    client.update_series({"id": 2}, timeout=1.0)
    client.delete_series(2, delete_files=True, timeout=1.0)
    client.get_episodes(9, timeout=1.0)
    client.get_episode(3, timeout=1.0)
    client.update_episode({"id": 3}, timeout=1.0)
    client.get_commands(timeout=1.0)
    client.run_command("RescanSeries", timeout=1.0, seriesId=2)
    client.get_queue(page=2, page_size=5, timeout=1.0)
    client.get_history(page=2, page_size=5, timeout=1.0)
    client.get_status(timeout=1.0)
    client.get_wanted_missing(page=2, page_size=5, timeout=1.0)
    client.get_wanted_cutoff(page=2, page_size=5, timeout=1.0)
    client.get_blocklist(page=2, page_size=5, timeout=1.0)
    client.get_blocklist_series(page=2, page_size=5, timeout=1.0)
    client.get_tags(timeout=1.0)
    client.get_root_folders(timeout=1.0)
    client.get_quality_profiles(timeout=1.0)

    assert client.calls == [
        ("GET", "series", {"params": None, "json_data": None, "timeout": 1.0}),
        ("GET", "series/2", {"params": None, "json_data": None, "timeout": 1.0}),
        ("GET", "series/lookup", {"params": {"term": "office"}, "json_data": None, "timeout": 1.0}),
        ("POST", "series", {"params": None, "json_data": {"title": "Office"}, "timeout": 1.0}),
        ("PUT", "series", {"params": None, "json_data": {"id": 2}, "timeout": 1.0}),
        ("DELETE", "series/2", {"params": {"deleteFiles": "true"}, "json_data": None, "timeout": 1.0}),
        ("GET", "episode", {"params": {"seriesId": 9}, "json_data": None, "timeout": 1.0}),
        ("GET", "episode/3", {"params": None, "json_data": None, "timeout": 1.0}),
        ("PUT", "episode", {"params": None, "json_data": {"id": 3}, "timeout": 1.0}),
        ("GET", "command", {"params": None, "json_data": None, "timeout": 1.0}),
        ("POST", "command", {"params": None, "json_data": {"name": "RescanSeries", "seriesId": 2}, "timeout": 1.0}),
        ("GET", "queue", {"params": {"page": 2, "pageSize": 5, "sortKey": "timeleft", "sortDirection": "ascending"}, "json_data": None, "timeout": 1.0}),
        ("GET", "history", {"params": {"page": 2, "pageSize": 5, "sortKey": "date", "sortDirection": "descending"}, "json_data": None, "timeout": 1.0}),
        ("GET", "system/status", {"params": None, "json_data": None, "timeout": 1.0}),
        ("GET", "wanted/missing", {"params": {"page": 2, "pageSize": 5, "sortKey": "airDateUtc", "sortDirection": "descending"}, "json_data": None, "timeout": 1.0}),
        ("GET", "wanted/cutoff", {"params": {"page": 2, "pageSize": 5}, "json_data": None, "timeout": 1.0}),
        ("GET", "blocklist", {"params": {"page": 2, "pageSize": 5}, "json_data": None, "timeout": 1.0}),
        ("GET", "history/series", {"params": {"page": 2, "pageSize": 5}, "json_data": None, "timeout": 1.0}),
        ("GET", "tag", {"params": None, "json_data": None, "timeout": 1.0}),
        ("GET", "rootfolder", {"params": None, "json_data": None, "timeout": 1.0}),
        ("GET", "qualityprofile", {"params": None, "json_data": None, "timeout": 1.0}),
    ]


def test_build_request_prefixes_api_path() -> None:
    client = SonarrClient("https://sonarr.example", "token")

    spec = client.build_request("POST", "series", json_data={"title": "Office"}, timeout=8.0)

    assert spec.to_dict() == {
        "method": "POST",
        "path": "/api/v3/series",
        "timeout": 8.0,
        "json_body": {"title": "Office"},
        "headers": {"X-Api-Key": "token"},
    }
