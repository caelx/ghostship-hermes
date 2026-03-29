from typing import Any, Dict, List, Optional
import httpx
import os


class SynologyClient:
    def __init__(
        self, base_url: str, username: str, password: str, verify_ssl: bool = True
    ):
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.verify_ssl = verify_ssl
        self.sid: Optional[str] = None
        self.api_info: Dict[str, Any] = {}

    def _request(
        self,
        api: str,
        method: str,
        version: int,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
    ) -> Any:
        url = f"{self.base_url}/webapi/{path}"
        query_params = {
            "api": api,
            "version": version,
            "method": method,
        }
        if params:
            query_params.update(params)

        if self.sid and api != "SYNO.API.Auth":
            query_params["_sid"] = self.sid

        with httpx.Client(verify=self.verify_ssl) as client:
            if files:
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
        data = self._request("SYNO.API.Info", "query", 1, "query.cgi", {"query": query})
        self.api_info.update(data)
        return data

    def login(self) -> str:
        # First get info if not already fetched
        if not self.api_info:
            self.get_info()

        auth_info = self.api_info.get("SYNO.API.Auth", {})
        version = auth_info.get("maxVersion", 6)
        path = auth_info.get("path", "auth.cgi")

        params = {
            "account": self.username,
            "passwd": self.password,
            "session": "FileStation",
            "format": "sid",
        }
        data = self._request("SYNO.API.Auth", "login", version, path, params)
        self.sid = data.get("sid")
        return self.sid

    def logout(self) -> bool:
        if not self.sid:
            return True
        auth_info = self.api_info.get("SYNO.API.Auth", {})
        version = auth_info.get("maxVersion", 6)
        path = auth_info.get("path", "auth.cgi")
        self._request(
            "SYNO.API.Auth", "logout", version, path, {"session": "FileStation"}
        )
        self.sid = None
        return True

    # File Station List
    def list_shares(self) -> Any:
        api = "SYNO.FileStation.List"
        info = self.api_info.get(api, {})
        return self._request(
            api, "list_share", info.get("maxVersion", 2), info.get("path", "entry.cgi")
        )

    def list_files(
        self, folder_path: str, offset: int = 0, limit: int = 100, sort_by: str = "name"
    ) -> Any:
        api = "SYNO.FileStation.List"
        info = self.api_info.get(api, {})
        params = {
            "folder_path": folder_path,
            "offset": offset,
            "limit": limit,
            "sort_by": sort_by,
        }
        return self._request(
            api,
            "list",
            info.get("maxVersion", 2),
            info.get("path", "entry.cgi"),
            params,
        )

    def get_file_info(self, path: str) -> Any:
        api = "SYNO.FileStation.List"
        info = self.api_info.get(api, {})
        return self._request(
            api,
            "getinfo",
            info.get("maxVersion", 2),
            info.get("path", "entry.cgi"),
            {"path": path},
        )

    # File Station Search
    def search_start(
        self, folder_path: str, pattern: str, recursive: bool = True
    ) -> str:
        api = "SYNO.FileStation.Search"
        info = self.api_info.get(api, {})
        params = {
            "folder_path": folder_path,
            "pattern": pattern,
            "recursive": str(recursive).lower(),
        }
        data = self._request(
            api,
            "start",
            info.get("maxVersion", 2),
            info.get("path", "entry.cgi"),
            params,
        )
        return data.get("taskid")

    def search_list(self, taskid: str, offset: int = 0, limit: int = 100) -> Any:
        api = "SYNO.FileStation.Search"
        info = self.api_info.get(api, {})
        params = {"taskid": taskid, "offset": offset, "limit": limit}
        return self._request(
            api,
            "list",
            info.get("maxVersion", 2),
            info.get("path", "entry.cgi"),
            params,
        )

    # File Station Create Folder
    def create_folder(
        self, folder_path: str, name: str, force_parent: bool = False
    ) -> Any:
        api = "SYNO.FileStation.CreateFolder"
        info = self.api_info.get(api, {})
        params = {
            "folder_path": folder_path,
            "name": name,
            "force_parent": str(force_parent).lower(),
        }
        return self._request(
            api,
            "create",
            info.get("maxVersion", 2),
            info.get("path", "entry.cgi"),
            params,
        )

    # File Station Rename
    def rename(self, path: str, name: str) -> Any:
        api = "SYNO.FileStation.Rename"
        info = self.api_info.get(api, {})
        params = {"path": path, "name": name}
        return self._request(
            api,
            "rename",
            info.get("maxVersion", 2),
            info.get("path", "entry.cgi"),
            params,
        )

    # File Station Delete
    def delete(self, path: str, recursive: bool = True) -> str:
        api = "SYNO.FileStation.Delete"
        info = self.api_info.get(api, {})
        params = {"path": path, "recursive": str(recursive).lower()}
        data = self._request(
            api,
            "start",
            info.get("maxVersion", 2),
            info.get("path", "entry.cgi"),
            params,
        )
        return data.get("taskid")

    # File Station Download
    def download_file(self, path: str, mode: str = "download") -> httpx.Response:
        api = "SYNO.FileStation.Download"
        info = self.api_info.get(api, {})
        url = f"{self.base_url}/webapi/{info.get('path', 'entry.cgi')}"
        params = {
            "api": api,
            "version": info.get("maxVersion", 2),
            "method": "download",
            "path": path,
            "mode": mode,
            "_sid": self.sid,
        }
        with httpx.Client(verify=self.verify_ssl) as client:
            response = client.get(url, params=params)
            response.raise_for_status()
            return response

    # File Station Upload
    def upload_file(
        self, folder_path: str, file_path: str, create_parents: bool = True
    ) -> Any:
        api = "SYNO.FileStation.Upload"
        info = self.api_info.get(api, {})
        url = f"{self.base_url}/webapi/{info.get('path', 'entry.cgi')}"
        params = {
            "api": api,
            "version": info.get("maxVersion", 2),
            "method": "upload",
            "path": folder_path,
            "create_parents": str(create_parents).lower(),
            "_sid": self.sid,
        }
        with httpx.Client(verify=self.verify_ssl) as client:
            with open(file_path, "rb") as f:
                files = {"file": (file_path.split("/")[-1], f)}
                response = client.post(url, params=params, files=files)
            response.raise_for_status()
            return response.json()

    # File Station Copy/Move
    def copy(self, path: str, destination: str, overwrite: bool = True) -> Any:
        api = "SYNO.FileStation.CopyMove"
        info = self.api_info.get(api, {})
        params = {
            "api": api,
            "version": info.get("maxVersion", 2),
            "method": "copy",
            "path": path,
            "destination": destination,
            "overwrite": str(overwrite).lower(),
            "_sid": self.sid,
        }
        url = f"{self.base_url}/webapi/{info.get('path', 'entry.cgi')}"
        with httpx.Client(verify=self.verify_ssl) as client:
            response = client.post(url, params=params)
            response.raise_for_status()
            return response.json()

    def move(self, path: str, destination: str, overwrite: bool = True) -> Any:
        api = "SYNO.FileStation.CopyMove"
        info = self.api_info.get(api, {})
        params = {
            "api": api,
            "version": info.get("maxVersion", 2),
            "method": "move",
            "path": path,
            "destination": destination,
            "overwrite": str(overwrite).lower(),
            "_sid": self.sid,
        }
        url = f"{self.base_url}/webapi/{info.get('path', 'entry.cgi')}"
        with httpx.Client(verify=self.verify_ssl) as client:
            response = client.post(url, params=params)
            response.raise_for_status()
            return response.json()
