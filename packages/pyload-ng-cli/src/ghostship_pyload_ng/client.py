from typing import Any, Dict, List, Optional
import httpx


class PyLoadClient:
    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url.rstrip("/")
        self.auth = (username, password)

    def _request(
        self,
        path: str,
        method: str = "GET",
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
    ) -> Any:
        url = f"{self.base_url}/{path.lstrip('/')}"
        with httpx.Client(auth=self.auth) as client:
            if method == "POST":
                response = client.post(url, params=params, json=json_data)
            elif method == "DELETE":
                response = client.delete(url, params=params)
            else:
                response = client.get(url, params=params)

            response.raise_for_status()
            if not response.content:
                return {"status": "success"}
            return response.json()

    def get_server_status(self) -> Any:
        return self._request("api/status_server")

    def get_downloads(self) -> Any:
        return self._request("api/status_downloads")

    def get_queue(self) -> Any:
        return self._request("api/get_queue")

    def add_package(self, name: str, links: List[str]) -> Any:
        return self._request(
            "api/add_package", method="POST", json_data={"name": name, "links": links}
        )

    def add_files(self, package_id: int, links: List[str]) -> Any:
        return self._request(
            "api/add_files",
            method="POST",
            json_data={"package_id": package_id, "links": links},
        )

    def delete_packages(self, package_ids: List[int]) -> Any:
        return self._request(
            "api/delete_packages", method="POST", json_data={"package_ids": package_ids}
        )

    def toggle_pause(self) -> Any:
        return self._request("api/toggle_pause", method="POST")

    def get_config(self) -> Any:
        return self._request("api/get_config_dict")

    # Downloads management
    def delete_finished(self) -> Any:
        return self._request("api/delete_finished", method="POST")

    def restart_failed(self) -> Any:
        return self._request("api/restart_failed", method="POST")

    def stop_all_downloads(self) -> Any:
        return self._request("api/stop_all_downloads", method="POST")

    # Accounts
    def get_accounts(self) -> Any:
        return self._request("api/get_accounts")

    def add_account(self, plugin: str, login: str, password: str) -> Any:
        return self._request(
            "api/update_account",
            method="POST",
            json_data={"plugin": plugin, "login": login, "password": password},
        )

    def remove_account(self, plugin: str, login: str) -> Any:
        return self._request(
            "api/remove_account",
            method="POST",
            json_data={"plugin": plugin, "login": login},
        )

    # Server
    def get_server_version(self) -> Any:
        return self._request("api/get_server_version")

    def get_free_space(self) -> Any:
        return self._request("api/free_space")
