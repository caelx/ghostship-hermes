from typing import Any, Dict, Optional

import httpx


class RommClient:
    def __init__(
        self,
        base_url: str,
        token: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ):
        self.base_url = base_url.rstrip("/")
        if "/api" not in self.base_url:
            self.base_url = f"{self.base_url}/api"
        self.token = token or self._authenticate(username=username, password=password)
        if not self.token:
            raise ValueError("RomM authentication requires a token or username/password.")
        self.headers = {"Authorization": f"Bearer {self.token}"}

    def _authenticate(self, username: Optional[str], password: Optional[str]) -> str:
        if not username or not password:
            raise ValueError(
                "Set ROMM_TOKEN or ROMM_USERNAME and ROMM_PASSWORD to authenticate."
            )

        response = httpx.post(
            f"{self.base_url}/token",
            data={
                "grant_type": "password",
                "username": username,
                "password": password,
            },
            timeout=30.0,
        )
        response.raise_for_status()
        payload = response.json()
        token = payload.get("access_token")
        if not token:
            raise ValueError("RomM /api/token response did not include access_token.")
        return token

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
                response = client.post(url, json=json_data, params=params)
            elif method == "PUT":
                response = client.put(url, json=json_data, params=params)
            elif method == "DELETE":
                response = client.delete(url, params=params)
            else:
                response = client.get(url, params=params)

            response.raise_for_status()
            if not response.content:
                return {"status": "success"}
            return response.json()

    def get_heartbeat(self) -> Any:
        return self._request("heartbeat")

    def get_platforms(self) -> Any:
        return self._request("platforms")

    def get_libraries(self) -> Any:
        return self._request("libraries")

    def get_roms(
        self, page: int = 1, page_size: int = 24, platform: Optional[str] = None
    ) -> Any:
        params = {"page": page, "page_size": page_size}
        if platform:
            params["platform"] = platform
        return self._request("roms", params=params)

    def get_rom(self, rom_id: int) -> Any:
        return self._request(f"roms/{rom_id}")

    def update_rom(self, rom_id: int, data: Dict[str, Any]) -> Any:
        return self._request(f"roms/{rom_id}", method="PUT", json_data=data)

    def delete_rom(self, rom_id: int) -> Any:
        return self._request(f"roms/{rom_id}", method="DELETE")

    def get_scans(self) -> Any:
        return self._request("scans")

    def start_scan(self, library_id: Optional[int] = None) -> Any:
        path = "scans" if library_id is None else f"scans/{library_id}"
        return self._request(path, method="POST")

    def get_collections(self) -> Any:
        return self._request("collections")

    def get_config(self) -> Any:
        return self._request("config")

    # Saves
    def get_saves(self, page: int = 1, page_size: int = 24) -> Any:
        params = {"page": page, "page_size": page_size}
        return self._request("saves", params=params)

    def get_saves_summary(self) -> Any:
        return self._request("saves/summary")

    def get_save(self, save_id: int) -> Any:
        return self._request(f"saves/{save_id}")

    # Users
    def get_users(self) -> Any:
        return self._request("users")

    def get_user_me(self) -> Any:
        return self._request("users/me")
