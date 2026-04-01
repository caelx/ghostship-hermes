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


class PyLoadClient:
    def __init__(self, base_url: str, username: str | None = None, password: str | None = None):
        self.base_url = base_url.rstrip("/")
        self.auth = (username, password) if username and password else None
        self.headers = _cloudflare_access_headers()

    def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json_data: dict[str, Any] | list[Any] | None = None,
    ) -> Any:
        url = f"{self.base_url}/{path.lstrip('/')}"
        with httpx.Client(auth=self.auth, headers=self.headers) as client:
            response = client.request(method.upper(), url, params=params, json=json_data)
            response.raise_for_status()
            if not response.content:
                return {"status": "success"}
            return response.json()

    def _request(
        self,
        path: str,
        method: str = "GET",
        params: dict[str, Any] | None = None,
        json_data: dict[str, Any] | list[Any] | None = None,
    ) -> Any:
        return self.request(method, path, params=params, json_data=json_data)

    def get_server_status(self) -> Any:
        return self._request("api/status_server")

    def get_downloads(self) -> Any:
        return self._request("api/status_downloads")

    def get_queue(self) -> Any:
        return self._request("api/get_queue")

    def add_package(self, name: str, links: list[str]) -> Any:
        return self._request("api/add_package", method="POST", json_data={"name": name, "links": links})

    def add_files(self, package_id: int, links: list[str]) -> Any:
        return self._request("api/add_files", method="POST", json_data={"package_id": package_id, "links": links})

    def delete_packages(self, package_ids: list[int]) -> Any:
        return self._request("api/delete_packages", method="POST", json_data={"package_ids": package_ids})

    def toggle_pause(self) -> Any:
        return self._request("api/toggle_pause", method="POST")

    def get_config(self) -> Any:
        return self._request("api/get_config_dict")

    def delete_finished(self) -> Any:
        return self._request("api/delete_finished", method="POST")

    def restart_failed(self) -> Any:
        return self._request("api/restart_failed", method="POST")

    def stop_all_downloads(self) -> Any:
        return self._request("api/stop_all_downloads", method="POST")

    def get_accounts(self, refresh: bool = False) -> Any:
        return self._request("api/get_accounts", params={"refresh": str(refresh).lower()})

    def add_account(self, plugin: str, login: str, password: str) -> Any:
        return self._request("api/update_account", method="POST", json_data={"plugin": plugin, "login": login, "password": password})

    def remove_account(self, plugin: str, login: str) -> Any:
        return self._request("api/remove_account", method="POST", json_data={"plugin": plugin, "login": login})

    def get_server_version(self) -> Any:
        return self._request("api/get_server_version")

    def get_free_space(self) -> Any:
        return self._request("api/free_space")
