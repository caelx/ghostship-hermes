from __future__ import annotations

from typing import Any

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


class RommClient:
    def __init__(self, base_url: str, token: str | None = None, username: str | None = None, password: str | None = None):
        self.base_url = base_url.rstrip("/")
        if "/api" not in self.base_url:
            self.base_url = f"{self.base_url}/api"
        self.cf_headers = _cloudflare_access_headers()
        self.token = token or self._authenticate(username=username, password=password)
        if not self.token:
            raise ValueError("RomM authentication requires a token or username/password.")
        self.headers = {**self.cf_headers, "Authorization": f"Bearer {self.token}"}

    def _authenticate(self, username: str | None, password: str | None) -> str:
        if not username or not password:
            raise ValueError("Set ROMM_TOKEN or ROMM_USERNAME and ROMM_PASSWORD to authenticate.")

        response = httpx.post(
            f"{self.base_url}/token",
            data={"grant_type": "password", "username": username, "password": password},
            timeout=30.0,
            headers=self.cf_headers,
        )
        response.raise_for_status()
        payload = response.json()
        token = payload.get("access_token")
        if not token:
            raise ValueError("RomM /api/token response did not include access_token.")
        return token

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
            if not response.content:
                return {"status": "success"}
            return response.json()

    def _request(self, path: str, method: str = "GET", params: dict[str, Any] | None = None, json_data: dict[str, Any] | list[Any] | None = None) -> Any:
        return self.request(method, path, params=params, json_data=json_data)

    def get_heartbeat(self) -> Any:
        return self._request("heartbeat")

    def get_platforms(self) -> Any:
        return self._request("platforms")

    def get_libraries(self) -> Any:
        return self._request("libraries")

    def get_roms(self, page: int = 1, page_size: int = 24, platform: str | None = None) -> Any:
        params = {"page": page, "page_size": page_size}
        if platform:
            params["platform"] = platform
        return self._request("roms", params=params)

    def get_rom(self, rom_id: int) -> Any:
        return self._request(f"roms/{rom_id}")

    def update_rom(self, rom_id: int, data: dict[str, Any]) -> Any:
        return self._request(f"roms/{rom_id}", method="PUT", json_data=data)

    def delete_rom(self, rom_id: int) -> Any:
        return self._request(f"roms/{rom_id}", method="DELETE")

    def get_scans(self) -> Any:
        return self._request("scans")

    def start_scan(self, library_id: int | None = None) -> Any:
        path = "scans" if library_id is None else f"scans/{library_id}"
        return self._request(path, method="POST")

    def get_collections(self) -> Any:
        return self._request("collections")

    def get_config(self) -> Any:
        return self._request("config")

    def get_saves(self, page: int = 1, page_size: int = 24) -> Any:
        return self._request("saves", params={"page": page, "page_size": page_size})

    def get_saves_summary(self) -> Any:
        return self._request("saves/summary")

    def get_save(self, save_id: int) -> Any:
        return self._request(f"saves/{save_id}")

    def get_users(self) -> Any:
        return self._request("users")

    def get_user_me(self) -> Any:
        return self._request("users/me")
