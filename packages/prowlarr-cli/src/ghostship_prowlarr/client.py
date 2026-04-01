from __future__ import annotations

from typing import Any

from ghostship_cli_contract import BaseHttpClient


class ProwlarrClient(BaseHttpClient):
    def __init__(self, base_url: str, api_key: str, *, default_timeout: float = 30.0):
        super().__init__(base_url, default_headers={"X-Api-Key": api_key}, default_timeout=default_timeout)

    def build_request(self, method: str, path: str, *, params: dict[str, Any] | None = None, json_data: dict[str, Any] | list[Any] | None = None, timeout: float | None = None):
        return self.build_request_spec(method, f"/api/v1/{path.lstrip('/')}", params=params, json_body=json_data, timeout=timeout)

    def request(self, method: str, path: str, *, params: dict[str, Any] | None = None, json_data: dict[str, Any] | list[Any] | None = None, timeout: float | None = None) -> Any:
        return self.request_json(method, f"/api/v1/{path.lstrip('/')}", params=params, json_body=json_data, timeout=timeout)

    def get_indexers(self, indexer_id: int | None = None, *, timeout: float | None = None) -> Any:
        path = "indexer" if indexer_id is None else f"indexer/{indexer_id}"
        return self.request("GET", path, timeout=timeout)

    def search(self, query: str, categories: list[int] | None = None, *, timeout: float | None = None) -> Any:
        params: dict[str, Any] = {"query": query}
        if categories:
            params["categories"] = categories
        return self.request("GET", "search", params=params, timeout=timeout)

    def get_applications(self, app_id: int | None = None, *, timeout: float | None = None) -> Any:
        path = "applications" if app_id is None else f"applications/{app_id}"
        return self.request("GET", path, timeout=timeout)

    def get_history(self, page: int = 1, page_size: int = 10, *, timeout: float | None = None) -> Any:
        return self.request("GET", "history", params={"page": page, "pageSize": page_size}, timeout=timeout)

    def get_status(self, *, timeout: float | None = None) -> Any:
        return self.request("GET", "system/status", timeout=timeout)

    def run_command(self, name: str, *, timeout: float | None = None, **kwargs: Any) -> Any:
        payload = {"name": name, **kwargs}
        return self.request("POST", "command", json_data=payload, timeout=timeout)

    def get_indexer_stats(self, *, timeout: float | None = None) -> Any:
        return self.request("GET", "indexerstats", timeout=timeout)

    def get_indexer_status(self, *, timeout: float | None = None) -> Any:
        return self.request("GET", "indexerstatus", timeout=timeout)
