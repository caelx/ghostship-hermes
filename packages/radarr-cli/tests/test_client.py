from __future__ import annotations

from ghostship_radarr.client import RadarrClient


class DummyRadarrClient(RadarrClient):
    def __init__(self) -> None:
        super().__init__("https://radarr.example", "token")
        self.calls: list[tuple[str, str, dict[str, object]]] = []

    def request(self, method: str, path: str, *, params=None, json_data=None):
        self.calls.append((method, path, {"params": params, "json_data": json_data}))
        return {"ok": True}


def test_wrappers_delegate_to_request() -> None:
    client = DummyRadarrClient()
    client.get_movies()
    client.get_movies(4)
    client.lookup_movie("inception")
    client.add_movie({"title": "Inception"})
    client.update_movie({"id": 4})
    client.delete_movie(4, delete_files=True)
    client.get_commands()
    client.run_command("MoviesSearch", movieIds=[4])
    client.get_queue(page=2, page_size=5)
    client.get_history(page=2, page_size=5)
    client.get_status()
    client.get_wanted_missing(page=2, page_size=5)
    client.get_wanted_cutoff(page=2, page_size=5)
    client.get_blocklist(page=2, page_size=5)
    client.get_blocklist_movie(page=2, page_size=5)
    client.get_tags()
    client.get_root_folders()
    client.get_quality_profiles()

    assert client.calls == [
        ("GET", "movie", {"params": None, "json_data": None}),
        ("GET", "movie/4", {"params": None, "json_data": None}),
        ("GET", "movie/lookup", {"params": {"term": "inception"}, "json_data": None}),
        ("POST", "movie", {"params": None, "json_data": {"title": "Inception"}}),
        ("PUT", "movie", {"params": None, "json_data": {"id": 4}}),
        ("DELETE", "movie/4", {"params": {"deleteFiles": "true"}, "json_data": None}),
        ("GET", "command", {"params": None, "json_data": None}),
        ("POST", "command", {"params": None, "json_data": {"name": "MoviesSearch", "movieIds": [4]}}),
        ("GET", "queue", {"params": {"page": 2, "pageSize": 5, "sortKey": "timeleft", "sortDirection": "ascending"}, "json_data": None}),
        ("GET", "history", {"params": {"page": 2, "pageSize": 5, "sortKey": "date", "sortDirection": "descending"}, "json_data": None}),
        ("GET", "system/status", {"params": None, "json_data": None}),
        ("GET", "wanted/missing", {"params": {"page": 2, "pageSize": 5, "sortKey": "releaseDate", "sortDirection": "descending"}, "json_data": None}),
        ("GET", "wanted/cutoff", {"params": {"page": 2, "pageSize": 5}, "json_data": None}),
        ("GET", "blocklist", {"params": {"page": 2, "pageSize": 5}, "json_data": None}),
        ("GET", "blocklist/movie", {"params": {"page": 2, "pageSize": 5}, "json_data": None}),
        ("GET", "tag", {"params": None, "json_data": None}),
        ("GET", "rootfolder", {"params": None, "json_data": None}),
        ("GET", "qualityprofile", {"params": None, "json_data": None}),
    ]
