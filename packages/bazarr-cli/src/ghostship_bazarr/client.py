from typing import Any, Dict, List, Optional
import httpx
import os


def _cloudflare_access_headers() -> dict[str, str]:
    headers: dict[str, str] = {}
    client_id = os.getenv("GHOSTSHIP_TEST_CF_ACCESS_CLIENT_ID")
    client_secret = os.getenv("GHOSTSHIP_TEST_CF_ACCESS_CLIENT_SECRET")
    if client_id:
        headers["CF-Access-Client-Id"] = client_id
    if client_secret:
        headers["CF-Access-Client-Secret"] = client_secret
    return headers


class BazarrClient:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip("/")
        if not self.base_url.endswith("/api"):
            self.base_url = f"{self.base_url}/api"
        self.api_key = api_key
        self.headers = _cloudflare_access_headers()
        self.headers["X-Api-Key"] = self.api_key

    def _request(
        self,
        path: str,
        method: str = "GET",
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
    ) -> Any:
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

    def get_badges(self) -> Any:
        return self._request("badges")

    def get_episodes(self, series_id: Optional[int] = None) -> Any:
        params = {}
        if series_id:
            params["seriesid[]"] = [series_id]
        return self._request("episodes", params=params)

    def get_wanted_episodes(self) -> Any:
        return self._request("episodes/wanted")

    def get_movies(self) -> Any:
        return self._request("movies")

    def get_wanted_movies(self) -> Any:
        return self._request("movies/wanted")

    def get_series(self) -> Any:
        return self._request("series")

    def get_providers(self) -> Any:
        return self._request("providers")

    def get_subtitles(self) -> Any:
        return self._request("subtitles")

    def get_system_health(self) -> Any:
        return self._request("system/health")

    def get_system_jobs(self) -> Any:
        return self._request("system/jobs")

    def get_system_tasks(self) -> Any:
        return self._request("system/tasks")

    def get_system_status(self) -> Any:
        return self._request("system/status")

    def search_subtitles_missing(self) -> Any:
        return self._request("subtitles/search/missing", method="POST")

    # History
    def get_episodes_history(self) -> Any:
        return self._request("episodes/history")

    def get_movies_history(self) -> Any:
        return self._request("movies/history")

    # Blacklist
    def get_episodes_blacklist(self) -> Any:
        return self._request("episodes/blacklist")

    def get_movies_blacklist(self) -> Any:
        return self._request("movies/blacklist")
