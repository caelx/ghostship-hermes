from __future__ import annotations

from typing import Any

from ghostship_cli_contract import BaseHttpClient


class SonarrClient(BaseHttpClient):
    def __init__(self, base_url: str, api_key: str, *, default_timeout: float = 30.0):
        super().__init__(base_url, default_headers={"X-Api-Key": api_key}, default_timeout=default_timeout)

    def build_request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json_data: dict[str, Any] | list[Any] | None = None,
        timeout: float | None = None,
    ):
        return self.build_request_spec(method, f"/api/v3/{path.lstrip('/')}", params=params, json_body=json_data, timeout=timeout)

    def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json_data: dict[str, Any] | list[Any] | None = None,
        timeout: float | None = None,
    ) -> Any:
        return self.request_json(method, f"/api/v3/{path.lstrip('/')}", params=params, json_body=json_data, timeout=timeout)

    def get_series(self, series_id: int | None = None, *, timeout: float | None = None) -> Any:
        path = "series" if series_id is None else f"series/{series_id}"
        return self.request("GET", path, timeout=timeout)

    def lookup_series(self, term: str, *, timeout: float | None = None) -> Any:
        return self.request("GET", "series/lookup", params={"term": term}, timeout=timeout)

    def add_series(self, series_data: dict[str, Any], *, timeout: float | None = None) -> Any:
        return self.request("POST", "series", json_data=series_data, timeout=timeout)

    def update_series(self, series_data: dict[str, Any], *, timeout: float | None = None) -> Any:
        return self.request("PUT", "series", json_data=series_data, timeout=timeout)

    def delete_series(self, series_id: int, delete_files: bool = False, *, timeout: float | None = None) -> Any:
        return self.request(
            "DELETE",
            f"series/{series_id}",
            params={"deleteFiles": str(delete_files).lower()},
            timeout=timeout,
        )

    def get_episodes(self, series_id: int, *, timeout: float | None = None) -> Any:
        return self.request("GET", "episode", params={"seriesId": series_id}, timeout=timeout)

    def get_episode(self, episode_id: int, *, timeout: float | None = None) -> Any:
        return self.request("GET", f"episode/{episode_id}", timeout=timeout)

    def update_episode(self, episode_data: dict[str, Any], *, timeout: float | None = None) -> Any:
        return self.request("PUT", "episode", json_data=episode_data, timeout=timeout)

    def get_commands(self, *, timeout: float | None = None) -> Any:
        return self.request("GET", "command", timeout=timeout)

    def run_command(self, name: str, *, timeout: float | None = None, **kwargs: Any) -> Any:
        payload = {"name": name, **kwargs}
        return self.request("POST", "command", json_data=payload, timeout=timeout)

    def get_queue(
        self,
        page: int = 1,
        page_size: int = 10,
        sort_key: str = "timeleft",
        sort_direction: str = "ascending",
        *,
        timeout: float | None = None,
    ) -> Any:
        return self.request(
            "GET",
            "queue",
            params={
                "page": page,
                "pageSize": page_size,
                "sortKey": sort_key,
                "sortDirection": sort_direction,
            },
            timeout=timeout,
        )

    def get_history(
        self,
        page: int = 1,
        page_size: int = 10,
        sort_key: str = "date",
        sort_direction: str = "descending",
        *,
        timeout: float | None = None,
    ) -> Any:
        return self.request(
            "GET",
            "history",
            params={
                "page": page,
                "pageSize": page_size,
                "sortKey": sort_key,
                "sortDirection": sort_direction,
            },
            timeout=timeout,
        )

    def get_status(self, *, timeout: float | None = None) -> Any:
        return self.request("GET", "system/status", timeout=timeout)

    def get_wanted_missing(
        self,
        page: int = 1,
        page_size: int = 10,
        sort_key: str = "airDateUtc",
        sort_direction: str = "descending",
        *,
        timeout: float | None = None,
    ) -> Any:
        return self.request(
            "GET",
            "wanted/missing",
            params={
                "page": page,
                "pageSize": page_size,
                "sortKey": sort_key,
                "sortDirection": sort_direction,
            },
            timeout=timeout,
        )

    def get_wanted_cutoff(self, page: int = 1, page_size: int = 10, *, timeout: float | None = None) -> Any:
        return self.request("GET", "wanted/cutoff", params={"page": page, "pageSize": page_size}, timeout=timeout)

    def get_blocklist(self, page: int = 1, page_size: int = 10, *, timeout: float | None = None) -> Any:
        return self.request("GET", "blocklist", params={"page": page, "pageSize": page_size}, timeout=timeout)

    def get_blocklist_series(self, page: int = 1, page_size: int = 10, *, timeout: float | None = None) -> Any:
        return self.request("GET", "history/series", params={"page": page, "pageSize": page_size}, timeout=timeout)

    def get_tags(self, *, timeout: float | None = None) -> Any:
        return self.request("GET", "tag", timeout=timeout)

    def get_root_folders(self, *, timeout: float | None = None) -> Any:
        return self.request("GET", "rootfolder", timeout=timeout)

    def get_quality_profiles(self, *, timeout: float | None = None) -> Any:
        return self.request("GET", "qualityprofile", timeout=timeout)
