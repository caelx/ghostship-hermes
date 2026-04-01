from __future__ import annotations

from ghostship_radarr.client import RadarrClient


class DummyRadarrClient(RadarrClient):
    def __init__(self) -> None:
        super().__init__("https://radarr.example", "token")
        self.calls: list[tuple[str, str, dict[str, object]]] = []

    def request(self, method: str, path: str, *, params=None, json_data=None, timeout=None):
        self.calls.append((method, path, {"params": params, "json_data": json_data, "timeout": timeout}))
        return {"ok": True}


def test_wrappers_delegate_to_request() -> None:
    client = DummyRadarrClient()
    client.get_movies(timeout=1.0)
    client.get_movies(2, timeout=1.0)
    client.lookup_movie("dune", timeout=1.0)
    client.add_movie({"title": "Dune"}, timeout=1.0)
    client.update_movie({"id": 2}, timeout=1.0)
    client.delete_movie(2, delete_files=True, timeout=1.0)
    client.get_commands(timeout=1.0)
    client.run_command("RefreshMovie", timeout=1.0, movieId=2)
    client.get_queue(page=2, page_size=5, timeout=1.0)
    client.get_history(page=2, page_size=5, timeout=1.0)
    client.get_status(timeout=1.0)
    client.get_wanted_missing(page=2, page_size=5, timeout=1.0)
    client.get_wanted_cutoff(page=2, page_size=5, timeout=1.0)
    client.get_blocklist(page=2, page_size=5, timeout=1.0)
    client.get_blocklist_movie(page=2, page_size=5, timeout=1.0)
    client.get_tags(timeout=1.0)
    client.get_root_folders(timeout=1.0)
    client.get_quality_profiles(timeout=1.0)

    assert client.calls == [
        ("GET", "movie", {"params": None, "json_data": None, "timeout": 1.0}),
        ("GET", "movie/2", {"params": None, "json_data": None, "timeout": 1.0}),
        ("GET", "movie/lookup", {"params": {"term": "dune"}, "json_data": None, "timeout": 1.0}),
        ("POST", "movie", {"params": None, "json_data": {"title": "Dune"}, "timeout": 1.0}),
        ("PUT", "movie", {"params": None, "json_data": {"id": 2}, "timeout": 1.0}),
        ("DELETE", "movie/2", {"params": {"deleteFiles": "true"}, "json_data": None, "timeout": 1.0}),
        ("GET", "command", {"params": None, "json_data": None, "timeout": 1.0}),
        ("POST", "command", {"params": None, "json_data": {"name": "RefreshMovie", "movieId": 2}, "timeout": 1.0}),
        ("GET", "queue", {"params": {"page": 2, "pageSize": 5, "sortKey": "timeleft", "sortDirection": "ascending"}, "json_data": None, "timeout": 1.0}),
        ("GET", "history", {"params": {"page": 2, "pageSize": 5, "sortKey": "date", "sortDirection": "descending"}, "json_data": None, "timeout": 1.0}),
        ("GET", "system/status", {"params": None, "json_data": None, "timeout": 1.0}),
        ("GET", "wanted/missing", {"params": {"page": 2, "pageSize": 5, "sortKey": "releaseDate", "sortDirection": "descending"}, "json_data": None, "timeout": 1.0}),
        ("GET", "wanted/cutoff", {"params": {"page": 2, "pageSize": 5}, "json_data": None, "timeout": 1.0}),
        ("GET", "blocklist", {"params": {"page": 2, "pageSize": 5}, "json_data": None, "timeout": 1.0}),
        ("GET", "blocklist/movie", {"params": {"page": 2, "pageSize": 5}, "json_data": None, "timeout": 1.0}),
        ("GET", "tag", {"params": None, "json_data": None, "timeout": 1.0}),
        ("GET", "rootfolder", {"params": None, "json_data": None, "timeout": 1.0}),
        ("GET", "qualityprofile", {"params": None, "json_data": None, "timeout": 1.0}),
    ]


def test_build_request_prefixes_api_path() -> None:
    client = RadarrClient("https://radarr.example", "token")
    spec = client.build_request("POST", "movie", json_data={"title": "Dune"}, timeout=8.0)
    assert spec.to_dict() == {"method": "POST", "path": "/api/v3/movie", "timeout": 8.0, "json_body": {"title": "Dune"}, "headers": {"X-Api-Key": "token"}}
