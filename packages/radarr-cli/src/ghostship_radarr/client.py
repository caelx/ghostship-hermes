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


class RadarrClient:
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

    def get_movies(self, movie_id: int | None = None) -> Any:
        path = "movie" if movie_id is None else f"movie/{movie_id}"
        return self.request("GET", path)

    def lookup_movie(self, term: str) -> Any:
        return self.request("GET", "movie/lookup", params={"term": term})

    def add_movie(self, movie_data: dict[str, Any]) -> Any:
        return self.request("POST", "movie", json_data=movie_data)

    def update_movie(self, movie_data: dict[str, Any]) -> Any:
        return self.request("PUT", "movie", json_data=movie_data)

    def delete_movie(self, movie_id: int, delete_files: bool = False) -> Any:
        return self.request(
            "DELETE",
            f"movie/{movie_id}",
            params={"deleteFiles": str(delete_files).lower()},
        )

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
        sort_key: str = "releaseDate",
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

    def get_blocklist_movie(self, page: int = 1, page_size: int = 10) -> Any:
        return self.request("GET", "blocklist/movie", params={"page": page, "pageSize": page_size})

    def get_tags(self) -> Any:
        return self.request("GET", "tag")

    def get_root_folders(self) -> Any:
        return self.request("GET", "rootfolder")

    def get_quality_profiles(self) -> Any:
        return self.request("GET", "qualityprofile")
