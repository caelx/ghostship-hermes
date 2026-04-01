from __future__ import annotations

from typing import Any
import os

import httpx


def _cloudflare_access_headers() -> dict[str, str]:
    headers: dict[str, str] = {}
    client_id = os.getenv("GHOSTSHIP_TEST_CF_ACCESS_CLIENT_ID")
    client_secret = os.getenv("GHOSTSHIP_TEST_CF_ACCESS_CLIENT_SECRET")
    if client_id:
        headers["CF-Access-Client-Id"] = client_id
    if client_secret:
        headers["CF-Access-Client-Secret"] = client_secret
    return headers


class SonarrClient:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.headers = _cloudflare_access_headers()
        self.headers["X-Api-Key"] = self.api_key

    def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json_data: dict[str, Any] | list[Any] | None = None,
    ) -> Any:
        url = f"{self.base_url}/api/v3/{path.lstrip('/')}"
        with httpx.Client(headers=self.headers) as client:
            response = client.request(method.upper(), url, params=params, json=json_data)
            response.raise_for_status()
            if not response.content:
                return {"status": "success"}
            return response.json()

    def get_series(self, series_id: int | None = None) -> Any:
        path = "series" if series_id is None else f"series/{series_id}"
        return self.request("GET", path)

    def lookup_series(self, term: str) -> Any:
        return self.request("GET", "series/lookup", params={"term": term})

    def add_series(self, series_data: dict[str, Any]) -> Any:
        return self.request("POST", "series", json_data=series_data)

    def update_series(self, series_data: dict[str, Any]) -> Any:
        return self.request("PUT", "series", json_data=series_data)

    def delete_series(self, series_id: int, delete_files: bool = False) -> Any:
        return self.request(
            "DELETE",
            f"series/{series_id}",
            params={"deleteFiles": str(delete_files).lower()},
        )

    def get_episodes(self, series_id: int) -> Any:
        return self.request("GET", "episode", params={"seriesId": series_id})

    def get_episode(self, episode_id: int) -> Any:
        return self.request("GET", f"episode/{episode_id}")

    def update_episode(self, episode_data: dict[str, Any]) -> Any:
        return self.request("PUT", "episode", json_data=episode_data)

    def get_commands(self) -> Any:
        return self.request("GET", "command")

    def run_command(self, name: str, **kwargs: Any) -> Any:
        payload = {"name": name, **kwargs}
        return self.request("POST", "command", json_data=payload)

    def get_queue(
        self,
        page: int = 1,
        page_size: int = 10,
        sort_key: str = "timeleft",
        sort_direction: str = "ascending",
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
        )

    def get_history(
        self,
        page: int = 1,
        page_size: int = 10,
        sort_key: str = "date",
        sort_direction: str = "descending",
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
        )

    def get_status(self) -> Any:
        return self.request("GET", "system/status")

    def get_wanted_missing(
        self,
        page: int = 1,
        page_size: int = 10,
        sort_key: str = "airDateUtc",
        sort_direction: str = "descending",
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
        )

    def get_wanted_cutoff(self, page: int = 1, page_size: int = 10) -> Any:
        return self.request("GET", "wanted/cutoff", params={"page": page, "pageSize": page_size})

    def get_blocklist(self, page: int = 1, page_size: int = 10) -> Any:
        return self.request("GET", "blocklist", params={"page": page, "pageSize": page_size})

    def get_blocklist_series(self, page: int = 1, page_size: int = 10) -> Any:
        return self.request("GET", "history/series", params={"page": page, "pageSize": page_size})

    def get_tags(self) -> Any:
        return self.request("GET", "tag")

    def get_root_folders(self) -> Any:
        return self.request("GET", "rootfolder")

    def get_quality_profiles(self) -> Any:
        return self.request("GET", "qualityprofile")
