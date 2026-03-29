from typing import Any, Dict, List, Optional
import httpx

class GrimmoryClient:
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.headers = {"Authorization": f"Bearer {self.token}"}

    def _request(self, path: str, method: str = "GET", params: Optional[Dict[str, Any]] = None, json_data: Optional[Dict[str, Any]] = None) -> Any:
        url = f"{self.base_url}/{path.lstrip('/')}"
        if not url.startswith(f"{self.base_url}/api/v1"):
             url = f"{self.base_url}/api/v1/{path.lstrip('/')}"
             
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
