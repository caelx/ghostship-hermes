from __future__ import annotations

import os
from typing import Any

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


class SynologyClient:
    def __init__(self, base_url: str, username: str, password: str, verify_ssl: bool = True):
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.verify_ssl = verify_ssl
        self.sid: str | None = None
        self.api_info: dict[str, Any] = {}
        self.headers = _cloudflare_access_headers()

    def call(
        self,
        api: str,
        method: str,
        *,
        version: int | None = None,
        path: str | None = None,
        params: dict[str, Any] | None = None,
        http_method: str | None = None,
        files: dict[str, Any] | None = None,
        use_sid: bool = True,
    ) -> Any:
        info = self.api_info.get(api, {})
        resolved_version = version if version is not None else info.get("maxVersion", 1)
        resolved_path = path if path is not None else info.get("path", "entry.cgi")
        query_params = {"api": api, "version": resolved_version, "method": method}
        if params:
            query_params.update(params)
        if use_sid and self.sid and api != "SYNO.API.Auth":
            query_params["_sid"] = self.sid
        transport_method = (http_method or ("POST" if files else "GET")).upper()
        url = f"{self.base_url}/webapi/{resolved_path}"
        with httpx.Client(verify=self.verify_ssl, headers=self.headers) as client:
            if transport_method == "POST":
                response = client.post(url, params=query_params, files=files)
            else:
                response = client.get(url, params=query_params)
            response.raise_for_status()
            data = response.json()
            if not data.get("success"):
                error_code = data.get("error", {}).get("code", "unknown")
                raise Exception(f"Synology API Error {error_code}: {data}")
            return data.get("data")

    def get_info(self, query: str = "all") -> Any:
        data = self.call("SYNO.API.Info", "query", version=1, path="query.cgi", params={"query": query}, use_sid=False)
        self.api_info.update(data)
        return data

    def login(self) -> str:
        if not self.api_info:
            self.get_info()
        auth_info = self.api_info.get("SYNO.API.Auth", {})
        data = self.call(
            "SYNO.API.Auth",
            "login",
            version=auth_info.get("maxVersion", 6),
            path=auth_info.get("path", "auth.cgi"),
            params={
                "account": self.username,
                "passwd": self.password,
                "session": "FileStation",
                "format": "sid",
            },
            use_sid=False,
        )
        self.sid = data.get("sid")
        return self.sid or ""

    def logout(self) -> bool:
        if not self.sid:
            return True
        auth_info = self.api_info.get("SYNO.API.Auth", {})
        self.call(
            "SYNO.API.Auth",
            "logout",
            version=auth_info.get("maxVersion", 6),
            path=auth_info.get("path", "auth.cgi"),
            params={"session": "FileStation"},
            use_sid=False,
        )
        self.sid = None
        return True

    def list_shares(self) -> Any:
        return self.call("SYNO.FileStation.List", "list_share")

    def list_files(self, folder_path: str, offset: int = 0, limit: int = 100, sort_by: str = "name") -> Any:
        return self.call(
            "SYNO.FileStation.List",
            "list",
            params={"folder_path": folder_path, "offset": offset, "limit": limit, "sort_by": sort_by},
        )

    def get_file_info(self, path: str) -> Any:
        return self.call("SYNO.FileStation.List", "getinfo", params={"path": path})

    def search_start(self, folder_path: str, pattern: str, recursive: bool = True) -> str:
        data = self.call(
            "SYNO.FileStation.Search",
            "start",
            params={"folder_path": folder_path, "pattern": pattern, "recursive": str(recursive).lower()},
        )
        return data.get("taskid")

    def search_list(self, taskid: str, offset: int = 0, limit: int = 100) -> Any:
        return self.call("SYNO.FileStation.Search", "list", params={"taskid": taskid, "offset": offset, "limit": limit})

    def create_folder(self, folder_path: str, name: str, force_parent: bool = False) -> Any:
        return self.call(
            "SYNO.FileStation.CreateFolder",
            "create",
            params={"folder_path": folder_path, "name": name, "force_parent": str(force_parent).lower()},
        )

    def rename(self, path: str, name: str) -> Any:
        return self.call("SYNO.FileStation.Rename", "rename", params={"path": path, "name": name})

    def delete(self, path: str, recursive: bool = True) -> str:
        data = self.call("SYNO.FileStation.Delete", "start", params={"path": path, "recursive": str(recursive).lower()})
        return data.get("taskid")

    def download_file(self, path: str, mode: str = "download") -> httpx.Response:
        info = self.api_info.get("SYNO.FileStation.Download", {})
        url = f"{self.base_url}/webapi/{info.get('path', 'entry.cgi')}"
        params = {
            "api": "SYNO.FileStation.Download",
            "version": info.get("maxVersion", 2),
            "method": "download",
            "path": path,
            "mode": mode,
            "_sid": self.sid,
        }
        with httpx.Client(verify=self.verify_ssl, headers=self.headers) as client:
            response = client.get(url, params=params)
            response.raise_for_status()
            return response

    def upload_file(self, folder_path: str, file_path: str, create_parents: bool = True) -> Any:
        info = self.api_info.get("SYNO.FileStation.Upload", {})
        with open(file_path, "rb") as handle:
            return self.call(
                "SYNO.FileStation.Upload",
                "upload",
                version=info.get("maxVersion", 2),
                path=info.get("path", "entry.cgi"),
                params={"path": folder_path, "create_parents": str(create_parents).lower()},
                http_method="POST",
                files={"file": (file_path.split("/")[-1], handle)},
            )

    def copy(self, path: str, destination: str, overwrite: bool = True) -> Any:
        return self.call(
            "SYNO.FileStation.CopyMove",
            "copy",
            params={"path": path, "destination": destination, "overwrite": str(overwrite).lower()},
            http_method="POST",
        )

    def move(self, path: str, destination: str, overwrite: bool = True) -> Any:
        return self.call(
            "SYNO.FileStation.CopyMove",
            "move",
            params={"path": path, "destination": destination, "overwrite": str(overwrite).lower()},
            http_method="POST",
        )
