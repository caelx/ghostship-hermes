from __future__ import annotations
from typing import Any
import json
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
class QBitClient:
    def __init__(self, base_url: str, username: str | None = None, password: str | None = None):
        self.base_url = base_url.rstrip("/")
        if "/api/v2" not in self.base_url:
            self.base_url = f"{self.base_url}/api/v2"
        self.username = username
        self.password = password
        self.cookies: httpx.Cookies | None = None
        self.headers = _cloudflare_access_headers()
    def login(self) -> bool:
        if not self.username or not self.password:
            return True
        url = f"{self.base_url}/auth/login"
        data = {"username": self.username, "password": self.password}
        with httpx.Client(headers=self.headers) as client:
            response = client.post(url, data=data)
            response.raise_for_status()
            if response.text == "Ok.":
                self.cookies = response.cookies
                return True
            return False
    def logout(self) -> bool:
        if not self.username or not self.password:
            return True
        return self._request("auth/logout", method="POST") == "Ok."
    def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        json_data: dict[str, Any] | list[Any] | None = None,
        files: dict[str, Any] | None = None,
    ) -> Any:
        if not self.cookies and self.username and self.password:
            self.login()
        url = f"{self.base_url}/{path.lstrip('/')}"
        with httpx.Client(cookies=self.cookies, headers=self.headers) as client:
            response = client.request(method.upper(), url, params=params, data=data, json=json_data, files=files)
            response.raise_for_status()
            if not response.content:
                return {"status": "success"}
            try:
                return response.json()
            except ValueError:
                return response.text
    def _request(
        self,
        path: str,
        method: str = "GET",
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        json_data: dict[str, Any] | list[Any] | None = None,
        files: dict[str, Any] | None = None,
    ) -> Any:
        return self.request(method, path, params=params, data=data, json_data=json_data, files=files)
    def get_app_version(self) -> str:
        return self._request("app/version")
    def get_api_version(self) -> str:
        return self._request("app/webapiVersion")
    def shutdown(self) -> bool:
        return self._request("app/shutdown", method="POST") == "Ok."
    def get_preferences(self) -> Any:
        return self._request("app/preferences")
    def set_preferences(self, prefs: dict[str, Any]) -> bool:
        data = {"json": json.dumps(prefs)}
        return self._request("app/setPreferences", method="POST", data=data) == "Ok."
    def get_log(self, last_known_id: int = -1) -> Any:
        return self._request("log/main", params={"last_id": last_known_id})
    def get_main_data(self, rid: int = 0) -> Any:
        return self._request("sync/maindata", params={"rid": rid})
    def get_transfer_info(self) -> Any:
        return self._request("transfer/info")
    def get_speed_limits_mode(self) -> int:
        return int(self._request("transfer/speedLimitsMode"))
    def toggle_speed_limits_mode(self) -> bool:
        return self._request("transfer/toggleSpeedLimitsMode", method="POST") == "Ok."
    def get_torrents(self, filter_type: str | None = None, category: str | None = None, sort: str | None = None, reverse: bool = False) -> Any:
        params = {}
        if filter_type:
            params["filter"] = filter_type
        if category:
            params["category"] = category
        if sort:
            params["sort"] = sort
        if reverse:
            params["reverse"] = str(reverse).lower()
        return self._request("torrents/info", params=params)
    def add_torrent(self, urls: list[str], save_path: str | None = None, category: str | None = None) -> bool:
        data = {"urls": "\n".join(urls)}
        if save_path:
            data["savepath"] = save_path
        if category:
            data["category"] = category
        return self._request("torrents/add", method="POST", data=data) == "Ok."
    def delete_torrents(self, hashes: list[str], delete_files: bool = False) -> bool:
        data = {"hashes": "|".join(hashes), "deleteFiles": str(delete_files).lower()}
        return self._request("torrents/delete", method="POST", data=data) == "Ok."
    def pause_torrents(self, hashes: list[str]) -> bool:
        return self._request("torrents/pause", method="POST", data={"hashes": "|".join(hashes)}) == "Ok."
    def resume_torrents(self, hashes: list[str]) -> bool:
        return self._request("torrents/resume", method="POST", data={"hashes": "|".join(hashes)}) == "Ok."
    def search_start(self, pattern: str, category: str = "all", plugins: str = "all") -> Any:
        return self._request("search/start", method="POST", data={"pattern": pattern, "category": category, "plugins": plugins})
    def search_status(self, search_id: int | None = None) -> Any:
        params = {}
        if search_id is not None:
            params["id"] = search_id
        return self._request("search/status", params=params)
    def search_results(self, search_id: int, limit: int = 10, offset: int = 0) -> Any:
        return self._request("search/results", params={"id": search_id, "limit": limit, "offset": offset})
    def get_rss_data(self, with_data: bool = True) -> Any:
        return self._request("rss/items", params={"withData": str(with_data).lower()})
