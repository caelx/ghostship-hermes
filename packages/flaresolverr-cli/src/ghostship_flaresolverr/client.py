import httpx
import os
from typing import Any, Optional


def _cloudflare_access_headers() -> dict[str, str]:
    headers: dict[str, str] = {}
    client_id = os.getenv("GHOSTSHIP_TEST_CF_ACCESS_CLIENT_ID")
    client_secret = os.getenv("GHOSTSHIP_TEST_CF_ACCESS_CLIENT_SECRET")
    if client_id:
        headers["CF-Access-Client-Id"] = client_id
    if client_secret:
        headers["CF-Access-Client-Secret"] = client_secret
    return headers


class FlareSolverrClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        if not self.base_url.endswith("/v1"):
             self.v1_url = f"{self.base_url}/v1"
        else:
             self.v1_url = self.base_url
        self.headers = _cloudflare_access_headers()

    def _post(self, cmd: str, **kwargs: Any) -> dict[str, Any]:
        payload = {"cmd": cmd, **kwargs}
        response = httpx.post(self.v1_url, json=payload, timeout=60.0, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def request_get(self, url: str, session: Optional[str] = None, **kwargs: Any) -> dict[str, Any]:
        return self._post("request.get", url=url, session=session, **kwargs)

    def request_post(self, url: str, post_data: str, session: Optional[str] = None, **kwargs: Any) -> dict[str, Any]:
        return self._post("request.post", url=url, postData=post_data, session=session, **kwargs)

    def sessions_create(self, session: Optional[str] = None, **kwargs: Any) -> dict[str, Any]:
        return self._post("sessions.create", session=session, **kwargs)

    def sessions_list(self) -> dict[str, Any]:
        return self._post("sessions.list")

    def sessions_destroy(self, session: str) -> dict[str, Any]:
        return self._post("sessions.destroy", session=session)
