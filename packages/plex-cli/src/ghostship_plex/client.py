from typing import Any, Dict, List, Optional
import httpx

class PlexClient:
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.headers = {
            "X-Plex-Token": self.token,
            "Accept": "application/json"
        }

    def _request(self, path: str, method: str = "GET", params: Optional[Dict[str, Any]] = None, json_data: Optional[Dict[str, Any]] = None) -> Any:
        url = f"{self.base_url}/{path.lstrip('/')}"
        with httpx.Client(headers=self.headers) as client:
            if method == "POST":
                response = client.post(url, params=params, json=json_data)
            elif method == "PUT":
                response = client.put(url, params=params, json=json_data)
            elif method == "DELETE":
                response = client.delete(url, params=params)
            else:
                response = client.get(url, params=params)
            
            response.raise_for_status()
            if response.status_code in [201, 204] or not response.content:
                return {"status": "success"}
            return response.json()

    # Identity and Status
    def get_identity(self) -> Any:
        return self._request("identity")

    def get_server_info(self) -> Any:
        return self._request("")

    def get_status_sessions(self) -> Any:
        return self._request("status/sessions")

    def get_activities(self) -> Any:
        return self._request("activities")

    # Library
    def get_library_sections(self) -> Any:
        return self._request("library/sections")

    def get_library_section(self, section_id: int) -> Any:
        return self._request(f"library/sections/{section_id}/all")

    def get_library_filters(self, section_id: int) -> Any:
        return self._request(f"library/sections/{section_id}/filters")

    def get_library_sorts(self, section_id: int) -> Any:
        return self._request(f"library/sections/{section_id}/sorts")

    def refresh_library(self, section_id: Optional[int] = None) -> Any:
        path = "library/sections/all/refresh" if section_id is None else f"library/sections/{section_id}/refresh"
        return self._request(path)

    def get_metadata(self, rating_key: int) -> Any:
        return self._request(f"library/metadata/{rating_key}")

    def get_metadata_children(self, rating_key: int) -> Any:
        return self._request(f"library/metadata/{rating_key}/children")

    # Playlists
    def get_playlists(self) -> Any:
        return self._request("playlists")

    def get_playlist_items(self, playlist_id: int) -> Any:
        return self._request(f"playlists/{playlist_id}/items")

    # Collections
    def get_collections(self, section_id: int) -> Any:
        return self._request(f"library/sections/{section_id}/collections")

    # Preferences
    def get_preferences(self) -> Any:
        return self._request(":/prefs")

    # Scheduled Tasks (Butler)
    def get_butler_tasks(self) -> Any:
        return self._request("butler")

    # System
    def get_statistics(self) -> Any:
        return self._request("statistics/resources", params={"timespan": 6})
