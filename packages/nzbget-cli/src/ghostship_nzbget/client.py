from typing import Any, Dict, List, Optional
import httpx


class NZBGetClient:
    def __init__(
        self,
        base_url: str,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ):
        self.base_url = base_url.rstrip("/")
        if not self.base_url.endswith("/jsonrpc"):
            self.base_url = f"{self.base_url}/jsonrpc"
        self.auth = (username, password) if username and password else None

    def _request(self, method: str, params: Optional[List[Any]] = None) -> Any:
        payload = {"version": "1.1", "method": method, "params": params or []}
        with httpx.Client(auth=self.auth) as client:
            response = client.post(self.base_url, json=payload)
            response.raise_for_status()
            data = response.json()
            if "error" in data and data["error"]:
                raise Exception(f"NZBGet API Error: {data['error']}")
            return data.get("result")

    # Program Control
    def get_version(self) -> str:
        return self._request("version")

    def shutdown(self) -> bool:
        return self._request("shutdown")

    def reload(self) -> bool:
        return self._request("reload")

    # Queue and History
    def get_status(self) -> Any:
        return self._request("status")

    def list_groups(self) -> Any:
        return self._request("listgroups")

    def list_files(self, nzb_id: int) -> Any:
        return self._request("listfiles", [0, 0, nzb_id])

    def get_history(self) -> Any:
        return self._request("history")

    def append_url(
        self, url: str, category: str = "", priority: int = 0, top: bool = False
    ) -> int:
        # string append(string Filename, string Content, string Category, int Priority, bool Top, bool Paused, string DupeKey, int DupeScore, string DupeMode)
        return self._request(
            "append", [url, "", category, priority, top, False, "", 0, "SCORE"]
        )

    def edit_queue(self, command: str, offset: int, size: int, ids: List[int]) -> bool:
        return self._request("editqueue", [command, offset, size, ids])

    def disk_scan(self) -> bool:
        return self._request("scan")

    # Status and Logging
    def get_log(self, id_from: int, count: int) -> Any:
        return self._request("log", [id_from, count])

    # Pause and Speed Limit
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

    # Configuration
    def get_config(self) -> Any:
        return self._request("config")

    def save_config(self, config: List[Dict[str, str]]) -> bool:
        # bool saveconfig(struct[] Config)
        return self._request("saveconfig", [config])
