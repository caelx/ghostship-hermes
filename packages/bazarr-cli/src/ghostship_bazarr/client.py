from typing import Any, Dict, List, Optional
import httpx

class BazarrClient:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip("/")
        if not self.base_url.endswith("/api"):
            self.base_url = f"{self.base_url}/api"
        self.api_key = api_key
        self.headers = {"X-Api-Key": self.api_key}

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
            if not response.content:
                return {"status": "success"}
            return response.json()

    def get_series(self) -> Any:
        return self._request("series")

    def get_movies(self) -> Any:
        return self._request("movies")

    def get_episodes(self, series_id: int) -> Any:
        return self._request("episodes", params={"seriesid": series_id})

    def search_subtitles_missing(self) -> Any:
        return self._request("subtitles/search/missing", method="POST")

    def get_system_status(self) -> Any:
        return self._request("system/status")
