from typing import Any, Dict, List, Optional
import httpx

class SonarrClient:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.headers = {"X-Api-Key": self.api_key}

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        url = f"{self.base_url}/api/v3/{path.lstrip('/')}"
        with httpx.Client(headers=self.headers) as client:
            response = client.get(url, params=params)
            response.raise_for_status()
            return response.json()

    def _post(self, path: str, json_data: Optional[Dict[str, Any]] = None, params: Optional[Dict[str, Any]] = None) -> Any:
        url = f"{self.base_url}/api/v3/{path.lstrip('/')}"
        with httpx.Client(headers=self.headers) as client:
            response = client.post(url, json=json_data, params=params)
            response.raise_for_status()
            return response.json()

    def _put(self, path: str, json_data: Optional[Dict[str, Any]] = None) -> Any:
        url = f"{self.base_url}/api/v3/{path.lstrip('/')}"
        with httpx.Client(headers=self.headers) as client:
            response = client.put(url, json=json_data)
            response.raise_for_status()
            return response.json()

    def _delete(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        url = f"{self.base_url}/api/v3/{path.lstrip('/')}"
        with httpx.Client(headers=self.headers) as client:
            response = client.delete(url, params=params)
            response.raise_for_status()
            return response.status_code == 200

    # Series
    def get_series(self, series_id: Optional[int] = None) -> Any:
        path = "series" if series_id is None else f"series/{series_id}"
        return self._get(path)

    def lookup_series(self, term: str) -> Any:
        return self._get("series/lookup", params={"term": term})

    def add_series(self, series_data: Dict[str, Any]) -> Any:
        return self._post("series", json_data=series_data)

    def update_series(self, series_data: Dict[str, Any]) -> Any:
        return self._put("series", json_data=series_data)

    def delete_series(self, series_id: int, delete_files: bool = False) -> Any:
        return self._delete(f"series/{series_id}", params={"deleteFiles": delete_files})

    # Episode
    def get_episodes(self, series_id: int) -> Any:
        return self._get("episode", params={"seriesId": series_id})

    def get_episode(self, episode_id: int) -> Any:
        return self._get(f"episode/{episode_id}")

    def update_episode(self, episode_data: Dict[str, Any]) -> Any:
        return self._put("episode", json_data=episode_data)

    # Command
    def get_commands(self) -> Any:
        return self._get("command")

    def run_command(self, name: str, **kwargs) -> Any:
        payload = {"name": name, **kwargs}
        return self._post("command", json_data=payload)

    # Queue
    def get_queue(self, page: int = 1, page_size: int = 10, sort_key: str = "timeleft", sort_direction: str = "ascending") -> Any:
        params = {
            "page": page,
            "pageSize": page_size,
            "sortKey": sort_key,
            "sortDirection": sort_direction
        }
        return self._get("queue", params=params)

    # History
    def get_history(self, page: int = 1, page_size: int = 10, sort_key: str = "date", sort_direction: str = "descending") -> Any:
        params = {
            "page": page,
            "pageSize": page_size,
            "sortKey": sort_key,
            "sortDirection": sort_direction
        }
        return self._get("history", params=params)

    # System
    def get_status(self) -> Any:
        return self._get("system/status")
