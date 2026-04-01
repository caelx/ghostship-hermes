from __future__ import annotations

from ghostship_sonarr.client import SonarrClient


class DummySonarrClient(SonarrClient):
    def __init__(self) -> None:
        super().__init__("https://sonarr.example", "token")
        self.calls: list[tuple[str, str, dict[str, object]]] = []

    def request(self, method: str, path: str, *, params=None, json_data=None):
        self.calls.append((method, path, {"params": params, "json_data": json_data}))
        return {"ok": True}


def test_wrappers_delegate_to_request() -> None:
    client = DummySonarrClient()
    client.get_series()
    client.get_series(2)
    client.lookup_series("office")
    client.add_series({"title": "Office"})
    client.update_series({"id": 2})
    client.delete_series(2, delete_files=True)
    client.get_episodes(9)
    client.get_episode(3)
    client.update_episode({"id": 3})
    client.get_commands()
    client.run_command("RescanSeries", seriesId=2)
    client.get_queue(page=2, page_size=5)
    client.get_history(page=2, page_size=5)
    client.get_status()
    client.get_wanted_missing(page=2, page_size=5)
    client.get_wanted_cutoff(page=2, page_size=5)
    client.get_blocklist(page=2, page_size=5)
    client.get_blocklist_series(page=2, page_size=5)
    client.get_tags()
    client.get_root_folders()
    client.get_quality_profiles()

    assert client.calls == [
        ("GET", "series", {"params": None, "json_data": None}),
        ("GET", "series/2", {"params": None, "json_data": None}),
        ("GET", "series/lookup", {"params": {"term": "office"}, "json_data": None}),
        ("POST", "series", {"params": None, "json_data": {"title": "Office"}}),
        ("PUT", "series", {"params": None, "json_data": {"id": 2}}),
        ("DELETE", "series/2", {"params": {"deleteFiles": "true"}, "json_data": None}),
        ("GET", "episode", {"params": {"seriesId": 9}, "json_data": None}),
        ("GET", "episode/3", {"params": None, "json_data": None}),
        ("PUT", "episode", {"params": None, "json_data": {"id": 3}}),
        ("GET", "command", {"params": None, "json_data": None}),
        ("POST", "command", {"params": None, "json_data": {"name": "RescanSeries", "seriesId": 2}}),
        ("GET", "queue", {"params": {"page": 2, "pageSize": 5, "sortKey": "timeleft", "sortDirection": "ascending"}, "json_data": None}),
        ("GET", "history", {"params": {"page": 2, "pageSize": 5, "sortKey": "date", "sortDirection": "descending"}, "json_data": None}),
        ("GET", "system/status", {"params": None, "json_data": None}),
        ("GET", "wanted/missing", {"params": {"page": 2, "pageSize": 5, "sortKey": "airDateUtc", "sortDirection": "descending"}, "json_data": None}),
        ("GET", "wanted/cutoff", {"params": {"page": 2, "pageSize": 5}, "json_data": None}),
        ("GET", "blocklist", {"params": {"page": 2, "pageSize": 5}, "json_data": None}),
        ("GET", "history/series", {"params": {"page": 2, "pageSize": 5}, "json_data": None}),
        ("GET", "tag", {"params": None, "json_data": None}),
        ("GET", "rootfolder", {"params": None, "json_data": None}),
        ("GET", "qualityprofile", {"params": None, "json_data": None}),
    ]
