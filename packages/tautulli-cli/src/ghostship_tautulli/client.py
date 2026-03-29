from typing import Any, Dict, List, Optional
import httpx

class TautulliClient:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip("/")
        if not self.base_url.endswith("/api/v2"):
            self.base_url = f"{self.base_url}/api/v2"
        self.api_key = api_key

    def _request(self, cmd: str, **kwargs) -> Any:
        params = {
            "apikey": self.api_key,
            "cmd": cmd
        }
        params.update(kwargs)
        with httpx.Client() as client:
            response = client.get(self.base_url, params=params)
            response.raise_for_status()
            data = response.json()
            if data.get("response", {}).get("result") != "success":
                raise Exception(f"Tautulli API Error: {data.get('response', {}).get('message')}")
            return data.get("response", {}).get("data")

    # Status and Info
    def get_server_status(self) -> Any:
        return self._request("server_status")

    def get_tautulli_info(self) -> Any:
        return self._request("get_tautulli_info")

    def get_status(self) -> Any:
        return self._request("status")

    # Activity
    def get_activity(self) -> Any:
        return self._request("get_activity")

    def terminate_session(self, session_id: str, message: Optional[str] = None) -> Any:
        kwargs = {"session_id": session_id}
        if message:
            kwargs["message"] = message
        return self._request("terminate_session", **kwargs)

    # History
    def get_history(self, page: int = 1, length: int = 10, search: Optional[str] = None, order_column: str = "date", order_dir: str = "desc") -> Any:
        kwargs = {
            "start": (page - 1) * length,
            "length": length,
            "order_column": order_column,
            "order_dir": order_dir
        }
        if search:
            kwargs["search"] = search
        return self._request("get_history", **kwargs)

    # Library
    def get_libraries(self) -> Any:
        return self._request("get_libraries")

    def get_library_user_stats(self, section_id: int) -> Any:
        return self._request("get_library_user_stats", section_id=section_id)

    # Users
    def get_users(self) -> Any:
        return self._request("get_users")

    def get_user_player_stats(self, user_id: int) -> Any:
        return self._request("get_user_player_stats", user_id=user_id)

    def get_user_watch_time_stats(self, user_id: int) -> Any:
        return self._request("get_user_watch_time_stats", user_id=user_id)

    # Metadata
    def get_metadata(self, rating_key: int) -> Any:
        return self._request("get_metadata", rating_key=rating_key)

    # Search
    def search(self, query: str, limit: int = 10) -> Any:
        return self._request("search", query=query, limit=limit)

    # System
    def restart(self) -> Any:
        return self._request("restart")
