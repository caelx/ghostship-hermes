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


class NZBGetClient:
    def __init__(self, base_url: str, username: str | None = None, password: str | None = None):
        self.base_url = base_url.rstrip("/")
        if not self.base_url.endswith("/jsonrpc"):
            self.base_url = f"{self.base_url}/jsonrpc"
        self.auth = (username, password) if username and password else None
        self.headers = _cloudflare_access_headers()

    def call(self, method: str, params: list[Any] | None = None) -> Any:
        payload = {"version": "1.1", "method": method, "params": params or []}
        with httpx.Client(auth=self.auth, headers=self.headers) as client:
            response = client.post(self.base_url, json=payload)
            response.raise_for_status()
            data = response.json()
            if "error" in data and data["error"]:
                raise Exception(f"NZBGet API Error: {data['error']}")
            return data.get("result")

    def _request(self, method: str, params: list[Any] | None = None) -> Any:
        return self.call(method, params=params)

    def get_version(self) -> str:
        return self._request("version")

    def shutdown(self) -> bool:
        return self._request("shutdown")

    def reload(self) -> bool:
        return self._request("reload")

    def get_status(self) -> Any:
        return self._request("status")

    def list_groups(self) -> Any:
        return self._request("listgroups")

    def list_files(self, nzb_id: int) -> Any:
        return self._request("listfiles", [0, 0, nzb_id])

    def get_history(self) -> Any:
        return self._request("history")

    def append_url(self, url: str, category: str = "", priority: int = 0, top: bool = False) -> int:
        return self._request("append", [url, "", category, priority, top, False, "", 0, "SCORE"])

    def edit_queue(self, command: str, offset: int, size: int, ids: list[int]) -> bool:
        return self._request("editqueue", [command, offset, size, ids])

    def disk_scan(self) -> bool:
        return self._request("scan")

    def get_log(self, id_from: int, count: int) -> Any:
        return self._request("log", [id_from, count])

    def set_rate(self, limit_kb: int) -> bool:
        return self._request("rate", [limit_kb])

    def pause_download(self) -> bool:
        return self._request("pausedownload")

    def resume_download(self) -> bool:
        return self._request("resumedownload")

    def pause_post(self) -> bool:
        return self._request("pausepost")

    def resume_post(self) -> bool:
        return self._request("resumepost")

    def pause_scan(self) -> bool:
        return self._request("pausescan")

    def resume_scan(self) -> bool:
        return self._request("resumescan")

    def get_config(self) -> Any:
        return self._request("config")

    def save_config(self, config: list[dict[str, str]]) -> bool:
        return self._request("saveconfig", [config])
