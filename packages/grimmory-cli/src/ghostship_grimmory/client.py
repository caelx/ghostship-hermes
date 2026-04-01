from typing import Any, Dict, Optional

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
    def __init__(
        self,
        base_url: str,
        token: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ):
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
            raise ValueError(
                "Grimmory authentication requires a token or username/password."
            )
        self.headers = {**self.cf_headers, "Authorization": f"Bearer {self.token}"}

    def _authenticate(self, username: Optional[str], password: Optional[str]) -> str:
        if not username or not password:
            raise ValueError(
                "Set GRIMMORY_TOKEN or GRIMMORY_USERNAME and GRIMMORY_PASSWORD."
            )

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
            raise ValueError(
                "Grimmory /api/v1/auth/login response did not include an access token."
            )
        return token

    def _request(
        self,
        path: str,
        method: str = "GET",
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
    ) -> Any:
        url = f"{self.api_base_url}/{path.lstrip('/')}"

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

    # Books
    def get_books(self, page: int = 0, size: int = 20, library_id: Optional[int] = None) -> Any:
        params = {"page": page, "size": size}
        if library_id:
            params["libraryId"] = library_id
        return self._request("books", params=params)

    def get_book(self, book_id: int) -> Any:
        return self._request(f"books/{book_id}")

    def download_book(self, book_id: int) -> Any:
        return self._request(f"books/{book_id}/download")

    # Libraries
    def get_libraries(self) -> Any:
        return self._request("libraries")

    def get_library(self, library_id: int) -> Any:
        return self._request(f"libraries/{library_id}")

    def scan_libraries(self) -> Any:
        return self._request("libraries/scan", method="POST")

    def refresh_library(self, library_id: int) -> Any:
        return self._request(f"libraries/{library_id}/refresh", method="PUT")

    # Authors
    def get_authors(self, page: int = 0, size: int = 20) -> Any:
        return self._request("authors", params={"page": page, "size": size})

    def get_author(self, author_id: int) -> Any:
        return self._request(f"authors/{author_id}")

    # Shelves
    def get_shelves(self) -> Any:
        return self._request("shelves")

    def get_shelf_books(self, shelf_id: int) -> Any:
        return self._request(f"shelves/{shelf_id}/books")

    # Tasks
    def get_tasks(self) -> Any:
        return self._request("tasks")

    def cancel_task(self, task_id: str) -> Any:
        return self._request(f"tasks/{task_id}/cancel", method="DELETE")

    # Version
    def get_version(self) -> Any:
        return self._request("version")
