from typing import Any, Dict, List, Optional
import httpx

class QBitClient:
    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url.rstrip("/")
        if "/api/v2" not in self.base_url:
            self.base_url = f"{self.base_url}/api/v2"
        self.username = username
        self.password = password
        self.cookies: Optional[httpx.Cookies] = None

    def login(self) -> bool:
        url = f"{self.base_url}/auth/login"
        data = {"username": self.username, "password": self.password}
        with httpx.Client() as client:
            response = client.post(url, data=data)
            response.raise_for_status()
            if response.text == "Ok.":
                self.cookies = response.cookies
                return True
            return False

    def logout(self) -> bool:
        return self._request("auth/logout", method="POST") == "Ok."

    def _request(self, path: str, method: str = "GET", params: Optional[Dict[str, Any]] = None, data: Optional[Dict[str, Any]] = None, files: Optional[Dict[str, Any]] = None) -> Any:
        if not self.cookies:
            self.login()
        
        url = f"{self.base_url}/{path.lstrip('/')}"
        with httpx.Client(cookies=self.cookies) as client:
            if method == "POST":
                response = client.post(url, data=data, params=params, files=files)
            else:
                response = client.get(url, params=params)
            
            response.raise_for_status()
            if not response.content:
                return {"status": "success"}
            try:
                return response.json()
            except:
                return response.text

    # Application
    def get_app_version(self) -> str:
        return self._request("app/version")

    def get_api_version(self) -> str:
        return self._request("app/webapiVersion")

    def shutdown(self) -> bool:
        return self._request("app/shutdown", method="POST") == "Ok."

    def get_preferences(self) -> Any:
        return self._request("app/preferences")

    def set_preferences(self, prefs: Dict[str, Any]) -> bool:
        data = {"json": json.dumps(prefs)}
        return self._request("app/setPreferences", method="POST", data=data) == "Ok."

    # Log
    def get_log(self, last_known_id: int = -1) -> Any:
        return self._request("log/main", params={"last_id": last_known_id})

    # Sync
    def get_main_data(self, rid: int = 0) -> Any:
        return self._request("sync/maindata", params={"rid": rid})

    # Transfer info
    def get_transfer_info(self) -> Any:
        return self._request("transfer/info")

    def get_speed_limits_mode(self) -> int:
        return int(self._request("transfer/speedLimitsMode"))

    def toggle_speed_limits_mode(self) -> bool:
        return self._request("transfer/toggleSpeedLimitsMode", method="POST") == "Ok."

    # Torrent management
    def get_torrents(self, filter_type: Optional[str] = None, category: Optional[str] = None, sort: Optional[str] = None, reverse: bool = False) -> Any:
        params = {}
        if filter_type: params["filter"] = filter_type
        if category: params["category"] = category
        if sort: params["sort"] = sort
        if reverse: params["reverse"] = str(reverse).lower()
        return self._request("torrents/info", params=params)

    def add_torrent(self, urls: List[str], save_path: Optional[str] = None, category: Optional[str] = None) -> bool:
        data = {"urls": "\n".join(urls)}
        if save_path:
            data["savepath"] = save_path
        if category:
            data["category"] = category
        return self._request("torrents/add", method="POST", data=data) == "Ok."

    def delete_torrents(self, hashes: List[str], delete_files: bool = False) -> bool:
        data = {"hashes": "|".join(hashes), "deleteFiles": str(delete_files).lower()}
        return self._request("torrents/delete", method="POST", data=data) == "Ok."

    def pause_torrents(self, hashes: List[str]) -> bool:
        data = {"hashes": "|".join(hashes)}
        return self._request("torrents/pause", method="POST", data=data) == "Ok."

    def resume_torrents(self, hashes: List[str]) -> bool:
        data = {"hashes": "|".join(hashes)}
        return self._request("torrents/resume", method="POST", data=data) == "Ok."

    # Search
    def search_start(self, pattern: str, category: str = "all", plugins: str = "all") -> Any:
        data = {"pattern": pattern, "category": category, "plugins": plugins}
        return self._request("search/start", method="POST", data=data)

    def search_status(self, search_id: Optional[int] = None) -> Any:
        params = {}
        if search_id is not None:
            params["id"] = search_id
        return self._request("search/status", params=params)

    def search_results(self, search_id: int, limit: int = 10, offset: int = 0) -> Any:
        params = {"id": search_id, "limit": limit, "offset": offset}
        return self._request("search/results", params=params)

    # RSS
    def get_rss_data(self, with_data: bool = True) -> Any:
        return self._request("rss/items", params={"withData": str(with_data).lower()})
