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


class PlexClient:
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.headers = _cloudflare_access_headers()
        self.headers.update({"X-Plex-Token": self.token, "Accept": "application/json"})

    def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json_data: dict[str, Any] | list[Any] | None = None,
    ) -> Any:
        url = f"{self.base_url}/{path.lstrip('/')}"
        with httpx.Client(headers=self.headers) as client:
            response = client.request(method.upper(), url, params=params, json=json_data)
            response.raise_for_status()
            if response.status_code in [201, 204] or not response.content:
                return {"status": "success"}
            return response.json()

    def _request(self, path: str, method: str = "GET", params: dict[str, Any] | None = None, json_data: dict[str, Any] | list[Any] | None = None) -> Any:
        return self.request(method, path, params=params, json_data=json_data)

    def get_identity(self) -> Any:
        return self._request("identity")

    def get_server_info(self) -> Any:
        return self._request("")

    def get_status_sessions(self) -> Any:
        return self._request("status/sessions")

    def get_activities(self) -> Any:
        return self._request("activities")

    def get_library_sections(self) -> Any:
        return self._request("library/sections")

    def get_library_section(self, section_id: int) -> Any:
        return self._request(f"library/sections/{section_id}/all")

    def get_library_filters(self, section_id: int) -> Any:
        return self._request(f"library/sections/{section_id}/filters")

    def get_library_sorts(self, section_id: int) -> Any:
        return self._request(f"library/sections/{section_id}/sorts")

    def refresh_library(self, section_id: int | None = None) -> Any:
        path = "library/sections/all/refresh" if section_id is None else f"library/sections/{section_id}/refresh"
        return self._request(path)

    def get_metadata(self, rating_key: int) -> Any:
        return self._request(f"library/metadata/{rating_key}")

    def get_metadata_children(self, rating_key: int) -> Any:
        return self._request(f"library/metadata/{rating_key}/children")

    def get_playlists(self) -> Any:
        return self._request("playlists")

    def get_playlist_items(self, playlist_id: int) -> Any:
        return self._request(f"playlists/{playlist_id}/items")

    def get_collections(self, section_id: int) -> Any:
        return self._request(f"library/sections/{section_id}/collections")

    def get_preferences(self) -> Any:
        return self._request(":/prefs")

    def get_butler_tasks(self) -> Any:
        return self._request("butler")

    def get_statistics(self) -> Any:
        return self._request("statistics/resources", params={"timespan": 6})

    def terminate_session(self, session_id: int) -> Any:
        return self._request(f"library/terminate/{session_id}", method="PUT")

    def get_session(self, session_id: int) -> Any:
        return self._request(f"sessions/{session_id}")
