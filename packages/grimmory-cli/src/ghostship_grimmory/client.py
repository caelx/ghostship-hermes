from __future__ import annotations

from typing import Any

import httpx
import os


def _cloudflare_access_headers() -> dict[str, str]:
    headers: dict[str, str] = {}
    client_id = os.getenv("GHOSTSHIP_TEST_CF_ACCESS_CLIENT_ID")
    client_secret = os.getenv("GHOSTSHIP_TEST_CF_ACCESS_CLIENT_SECRET")
    if client_id:
        headers["CF-Access-Client-Id"] = client_id
    if client_secret:
        headers["CF-Access-Client-Secret"] = client_secret
    return headers


class GrimmoryClient:
    def __init__(self, base_url: str, token: str | None = None, username: str | None = None, password: str | None = None):
        normalized_base_url = base_url.rstrip("/")
        if normalized_base_url.endswith("/api/v1"):
            self.base_url = normalized_base_url[: -len("/api/v1")]
            self.api_base_url = normalized_base_url
        else:
            self.base_url = normalized_base_url
            self.api_base_url = f"{normalized_base_url}/api/v1"

        self.cf_headers = _cloudflare_access_headers()
        self.token = token or self._authenticate(username=username, password=password)
        if not self.token:
            raise ValueError("Grimmory authentication requires a token or username/password.")
        self.headers = {**self.cf_headers, "Authorization": f"Bearer {self.token}"}

    def _authenticate(self, username: str | None, password: str | None) -> str:
        if not username or not password:
            raise ValueError("Set GRIMMORY_TOKEN or GRIMMORY_USERNAME and GRIMMORY_PASSWORD.")

        response = httpx.post(
            f"{self.api_base_url}/auth/login",
            json={"username": username, "password": password},
            timeout=30.0,
            headers=self.cf_headers,
        )
        response.raise_for_status()
        payload = response.json()
        token = payload.get("accessToken") or payload.get("access_token")
        if not token:
            raise ValueError("Grimmory /api/v1/auth/login response did not include an access token.")
        return token

    def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json_data: dict[str, Any] | list[Any] | None = None,
    ) -> Any:
        url = f"{self.api_base_url}/{path.lstrip('/')}"
        with httpx.Client(headers=self.headers) as client:
            response = client.request(method.upper(), url, params=params, json=json_data)
            response.raise_for_status()
            if not response.content:
                return {"status": "success"}
            return response.json()

    def _request(self, path: str, method: str = "GET", params: dict[str, Any] | None = None, json_data: dict[str, Any] | list[Any] | None = None) -> Any:
        return self.request(method, path, params=params, json_data=json_data)

    def get_books(self, page: int = 0, size: int = 20, library_id: int | None = None) -> Any:
        params = {"page": page, "size": size}
        if library_id:
            params["libraryId"] = library_id
        return self._request("books", params=params)

    def get_book(self, book_id: int) -> Any:
        return self._request(f"books/{book_id}")

    def download_book(self, book_id: int) -> Any:
        return self._request(f"books/{book_id}/download")

    def get_libraries(self) -> Any:
        return self._request("libraries")

    def get_library(self, library_id: int) -> Any:
        return self._request(f"libraries/{library_id}")

    def scan_libraries(self) -> Any:
        return self._request("libraries/scan", method="POST")

    def refresh_library(self, library_id: int) -> Any:
        return self._request(f"libraries/{library_id}/refresh", method="PUT")

    def get_authors(self, page: int = 0, size: int = 20) -> Any:
        return self._request("authors", params={"page": page, "size": size})

    def get_author(self, author_id: int) -> Any:
        return self._request(f"authors/{author_id}")

    def get_shelves(self) -> Any:
        return self._request("shelves")

    def get_shelf_books(self, shelf_id: int) -> Any:
        return self._request(f"shelves/{shelf_id}/books")

    def get_tasks(self) -> Any:
        return self._request("tasks")

    def cancel_task(self, task_id: str) -> Any:
        return self._request(f"tasks/{task_id}/cancel", method="DELETE")

    def get_version(self) -> Any:
        return self._request("version")
