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


class ProwlarrClient:
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
        url = f"{self.base_url}/api/v1/{path.lstrip('/')}"
        with httpx.Client(headers=self.headers) as client:
            response = client.request(method.upper(), url, params=params, json=json_data)
            response.raise_for_status()
            if not response.content:
                return {"status": "success"}
            return response.json()

    def get_indexers(self, indexer_id: int | None = None) -> Any:
        path = "indexer" if indexer_id is None else f"indexer/{indexer_id}"
        return self.request("GET", path)

    def search(self, query: str, categories: list[int] | None = None) -> Any:
        params: dict[str, Any] = {"query": query}
        if categories:
            params["categories"] = categories
        return self.request("GET", "search", params=params)

    def get_applications(self, app_id: int | None = None) -> Any:
        path = "applications" if app_id is None else f"applications/{app_id}"
        return self.request("GET", path)

    def get_history(self, page: int = 1, page_size: int = 10) -> Any:
        return self.request("GET", "history", params={"page": page, "pageSize": page_size})

    def get_status(self) -> Any:
        return self.request("GET", "system/status")

    def run_command(self, name: str, **kwargs: Any) -> Any:
        payload = {"name": name, **kwargs}
        return self.request("POST", "command", json_data=payload)

    def get_indexer_stats(self) -> Any:
        return self.request("GET", "indexerstats")

    def get_indexer_status(self) -> Any:
        return self.request("GET", "indexerstatus")
