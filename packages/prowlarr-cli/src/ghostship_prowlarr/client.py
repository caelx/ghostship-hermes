from typing import Any, Dict, List, Optional
import httpx


class ProwlarrClient:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.headers = {"X-Api-Key": self.api_key}

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        url = f"{self.base_url}/api/v1/{path.lstrip('/')}"
        with httpx.Client(headers=self.headers) as client:
            response = client.get(url, params=params)
            response.raise_for_status()
            return response.json()

    def _post(
        self,
        path: str,
        json_data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Any:
        url = f"{self.base_url}/api/v1/{path.lstrip('/')}"
        with httpx.Client(headers=self.headers) as client:
            response = client.post(url, json=json_data, params=params)
            response.raise_for_status()
            return response.json()

    def _put(self, path: str, json_data: Optional[Dict[str, Any]] = None) -> Any:
        url = f"{self.base_url}/api/v1/{path.lstrip('/')}"
        with httpx.Client(headers=self.headers) as client:
            response = client.put(url, json=json_data)
            response.raise_for_status()
            return response.json()

    def _delete(self, path: str, params: Optional[Dict[str, Any]] = None) -> Any:
        url = f"{self.base_url}/api/v1/{path.lstrip('/')}"
        with httpx.Client(headers=self.headers) as client:
            response = client.delete(url, params=params)
            response.raise_for_status()
            return response.status_code == 200

    # Indexer
    def get_indexers(self, indexer_id: Optional[int] = None) -> Any:
        path = "indexer" if indexer_id is None else f"indexer/{indexer_id}"
        return self._get(path)

    # Search
    def search(self, query: str, categories: Optional[List[int]] = None) -> Any:
        params = {"query": query}
        if categories:
            params["categories"] = categories
        return self._get("search", params=params)

    # Applications
    def get_applications(self, app_id: Optional[int] = None) -> Any:
        path = "application" if app_id is None else f"application/{app_id}"
        return self._get(path)

    # History
    def get_history(self, page: int = 1, page_size: int = 10) -> Any:
        params = {"page": page, "pageSize": page_size}
        return self._get("history", params=params)

    # System
    def get_status(self) -> Any:
        return self._get("system/status")

    # Command
    def run_command(self, name: str, **kwargs) -> Any:
        payload = {"name": name, **kwargs}
        return self._post("command", json_data=payload)

    # Indexer Stats
    def get_indexer_stats(self) -> Any:
        return self._get("indexerstats")

    def get_indexer_status(self) -> Any:
        return self._get("indexerstatus")
