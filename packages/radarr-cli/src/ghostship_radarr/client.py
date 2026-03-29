from typing import Any, Dict, List, Optional
import httpx

class RadarrClient:
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

    # Movie
    def get_movies(self, movie_id: Optional[int] = None) -> Any:
        path = "movie" if movie_id is None else f"movie/{movie_id}"
        return self._get(path)

    def lookup_movie(self, term: str) -> Any:
        return self._get("movie/lookup", params={"term": term})

    def add_movie(self, movie_data: Dict[str, Any]) -> Any:
        return self._post("movie", json_data=movie_data)

    def update_movie(self, movie_data: Dict[str, Any]) -> Any:
        return self._put("movie", json_data=movie_data)

    def delete_movie(self, movie_id: int, delete_files: bool = False) -> Any:
        return self._delete(f"movie/{movie_id}", params={"deleteFiles": delete_files})

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
