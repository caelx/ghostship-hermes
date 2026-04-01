from __future__ import annotations

from ghostship_bazarr.client import BazarrClient


class DummyBazarrClient(BazarrClient):
    def __init__(self) -> None:
        super().__init__("https://bazarr.example", "token")
        self.calls: list[tuple[str, str, dict[str, object]]] = []

    def request(self, method: str, path: str, *, params=None, json_data=None):
        self.calls.append((method, path, {"params": params, "json_data": json_data}))
        return {"ok": True}


def test_wrappers_delegate_to_request() -> None:
    client = DummyBazarrClient()
    client.get_badges()
    client.get_episodes(series_id=4)
    client.get_wanted_episodes()
    client.get_movies()
    client.get_wanted_movies()
    client.get_series()
    client.get_providers()
    client.get_subtitles()
    client.get_system_health()
    client.get_system_jobs()
    client.get_system_tasks()
    client.get_system_status()
    client.search_subtitles_missing()
    client.get_episodes_history()
    client.get_movies_history()
    client.get_episodes_blacklist()
    client.get_movies_blacklist()

    assert client.calls == [
        ("GET", "badges", {"params": None, "json_data": None}),
        ("GET", "episodes", {"params": {"seriesid[]": [4]}, "json_data": None}),
        ("GET", "episodes/wanted", {"params": None, "json_data": None}),
        ("GET", "movies", {"params": None, "json_data": None}),
        ("GET", "movies/wanted", {"params": None, "json_data": None}),
        ("GET", "series", {"params": None, "json_data": None}),
        ("GET", "providers", {"params": None, "json_data": None}),
        ("GET", "subtitles", {"params": None, "json_data": None}),
        ("GET", "system/health", {"params": None, "json_data": None}),
        ("GET", "system/jobs", {"params": None, "json_data": None}),
        ("GET", "system/tasks", {"params": None, "json_data": None}),
        ("GET", "system/status", {"params": None, "json_data": None}),
        ("POST", "subtitles/search/missing", {"params": None, "json_data": None}),
        ("GET", "episodes/history", {"params": None, "json_data": None}),
        ("GET", "movies/history", {"params": None, "json_data": None}),
        ("GET", "episodes/blacklist", {"params": None, "json_data": None}),
        ("GET", "movies/blacklist", {"params": None, "json_data": None}),
    ]
