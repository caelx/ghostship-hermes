from __future__ import annotations

from ghostship_bazarr.client import BazarrClient


class DummyBazarrClient(BazarrClient):
    def __init__(self) -> None:
        super().__init__("https://bazarr.example", "token")
        self.calls: list[tuple[str, str, dict[str, object]]] = []

    def request(self, method: str, path: str, *, params=None, json_data=None, timeout=None):
        self.calls.append((method, path, {"params": params, "json_data": json_data, "timeout": timeout}))
        return {"ok": True}


def test_wrappers_delegate_to_request() -> None:
    client = DummyBazarrClient()
    client.get_badges(timeout=1.0)
    client.get_episodes(timeout=1.0)
    client.get_episodes(series_id=4, timeout=1.0)
    client.get_wanted_episodes(timeout=1.0)
    client.get_movies(timeout=1.0)
    client.get_wanted_movies(timeout=1.0)
    client.get_series(timeout=1.0)
    client.get_providers(timeout=1.0)
    client.get_subtitles(timeout=1.0)
    client.get_system_health(timeout=1.0)
    client.get_system_jobs(timeout=1.0)
    client.get_system_tasks(timeout=1.0)
    client.get_system_status(timeout=1.0)
    client.search_subtitles_missing(timeout=1.0)
    client.get_episodes_history(timeout=1.0)
    client.get_movies_history(timeout=1.0)
    client.get_episodes_blacklist(timeout=1.0)
    client.get_movies_blacklist(timeout=1.0)

    assert client.calls[0] == ("GET", "badges", {"params": None, "json_data": None, "timeout": 1.0})
    assert client.calls[2] == ("GET", "episodes", {"params": {"seriesid[]": [4]}, "json_data": None, "timeout": 1.0})
    assert client.calls[13] == ("POST", "subtitles/search/missing", {"params": None, "json_data": None, "timeout": 1.0})


def test_build_request_prefixes_api_path() -> None:
    client = BazarrClient("https://bazarr.example", "token")
    spec = client.build_request("POST", "subtitles/search/missing", timeout=8.0)
    assert spec.to_dict() == {"method": "POST", "path": "/subtitles/search/missing", "timeout": 8.0, "headers": {"X-Api-Key": "token"}}
