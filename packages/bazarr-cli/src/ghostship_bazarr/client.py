from __future__ import annotations

from typing import Any

from ghostship_cli_contract import BaseHttpClient


class BazarrClient(BaseHttpClient):
    def __init__(self, base_url: str, api_key: str, *, default_timeout: float = 30.0):
        normalized = base_url.rstrip("/")
        if not normalized.endswith("/api"):
            normalized = f"{normalized}/api"
        super().__init__(normalized, default_headers={"X-Api-Key": api_key}, default_timeout=default_timeout)

    def build_request(self, method: str, path: str, *, params: dict[str, Any] | None = None, json_data: dict[str, Any] | list[Any] | None = None, timeout: float | None = None):
        return self.build_request_spec(method, f"/{path.lstrip('/')}", params=params, json_body=json_data, timeout=timeout)

    def request(self, method: str, path: str, *, params: dict[str, Any] | None = None, json_data: dict[str, Any] | list[Any] | None = None, timeout: float | None = None) -> Any:
        return self.request_json(method, f"/{path.lstrip('/')}", params=params, json_body=json_data, timeout=timeout)

    def _request(self, path: str, method: str = "GET", params: dict[str, Any] | None = None, json_data: dict[str, Any] | list[Any] | None = None, *, timeout: float | None = None) -> Any:
        return self.request(method, path, params=params, json_data=json_data, timeout=timeout)

    def get_badges(self, *, timeout: float | None = None) -> Any:
        return self._request("badges", timeout=timeout)

    def get_episodes(self, series_id: int | None = None, *, timeout: float | None = None) -> Any:
        params = {}
        if series_id:
            params["seriesid[]"] = [series_id]
        return self._request("episodes", params=params, timeout=timeout)

    def get_wanted_episodes(self, *, timeout: float | None = None) -> Any:
        return self._request("episodes/wanted", timeout=timeout)

    def get_movies(self, *, timeout: float | None = None) -> Any:
        return self._request("movies", timeout=timeout)

    def get_wanted_movies(self, *, timeout: float | None = None) -> Any:
        return self._request("movies/wanted", timeout=timeout)

    def get_series(self, *, timeout: float | None = None) -> Any:
        return self._request("series", timeout=timeout)

    def get_providers(self, *, timeout: float | None = None) -> Any:
        return self._request("providers", timeout=timeout)

    def get_subtitles(self, *, timeout: float | None = None) -> Any:
        return self._request("subtitles", timeout=timeout)

    def get_system_health(self, *, timeout: float | None = None) -> Any:
        return self._request("system/health", timeout=timeout)

    def get_system_jobs(self, *, timeout: float | None = None) -> Any:
        return self._request("system/jobs", timeout=timeout)

    def get_system_tasks(self, *, timeout: float | None = None) -> Any:
        return self._request("system/tasks", timeout=timeout)

    def get_system_status(self, *, timeout: float | None = None) -> Any:
        return self._request("system/status", timeout=timeout)

    def search_subtitles_missing(self, *, timeout: float | None = None) -> Any:
        return self._request("subtitles/search/missing", method="POST", timeout=timeout)

    def get_episodes_history(self, *, timeout: float | None = None) -> Any:
        return self._request("episodes/history", timeout=timeout)

    def get_movies_history(self, *, timeout: float | None = None) -> Any:
        return self._request("movies/history", timeout=timeout)

    def get_episodes_blacklist(self, *, timeout: float | None = None) -> Any:
        return self._request("episodes/blacklist", timeout=timeout)

    def get_movies_blacklist(self, *, timeout: float | None = None) -> Any:
        return self._request("movies/blacklist", timeout=timeout)
