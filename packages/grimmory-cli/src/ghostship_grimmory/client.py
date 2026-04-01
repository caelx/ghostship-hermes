from __future__ import annotations

from typing import Any

from ghostship_cli_contract import BaseHttpClient, ConfigError, RequestSpec


class GrimmoryClient(BaseHttpClient):
    def __init__(self, base_url: str, token: str | None = None, username: str | None = None, password: str | None = None, *, default_timeout: float = 30.0):
        normalized_base_url = base_url.rstrip('/')
        if normalized_base_url.endswith('/api/v1'):
            api_base_url = normalized_base_url
        else:
            api_base_url = f'{normalized_base_url}/api/v1'
        resolved_token = token or self._authenticate(api_base_url, username=username, password=password, timeout=default_timeout)
        if not resolved_token:
            raise ConfigError('Grimmory authentication requires a token or username/password.')
        super().__init__(api_base_url, default_headers={'Authorization': f'Bearer {resolved_token}'}, default_timeout=default_timeout)

    @staticmethod
    def _authenticate(api_base_url: str, *, username: str | None, password: str | None, timeout: float) -> str:
        if not username or not password:
            raise ConfigError('Set GRIMMORY_TOKEN or GRIMMORY_USERNAME and GRIMMORY_PASSWORD.')
        payload = BaseHttpClient(api_base_url, default_timeout=timeout).request_json('POST', '/auth/login', json_body={'username': username, 'password': password}, timeout=timeout)
        token = payload.get('accessToken') or payload.get('access_token')
        if not token:
            raise ConfigError('Grimmory /api/v1/auth/login response did not include an access token.')
        return str(token)

    def build_request(self, method: str, path: str, *, params: dict[str, Any] | None = None, json_data: dict[str, Any] | list[Any] | None = None, timeout: float | None = None) -> RequestSpec:
        return self.build_request_spec(method, path, params=params, json_body=json_data, timeout=timeout)

    def request(self, method: str, path: str, *, params: dict[str, Any] | None = None, json_data: dict[str, Any] | list[Any] | None = None, timeout: float | None = None) -> Any:
        spec = self.build_request(method, path, params=params, json_data=json_data, timeout=timeout)
        return self.request_json(spec.method, spec.path, params=spec.params, json_body=spec.json_body, timeout=spec.timeout)

    def get_books(self, page: int = 0, size: int = 20, library_id: int | None = None, timeout: float | None = None) -> Any:
        params = {'page': page, 'size': size}
        if library_id is not None:
            params['libraryId'] = library_id
        return self.request('GET', 'books', params=params, timeout=timeout)

    def get_book(self, book_id: int, timeout: float | None = None) -> Any:
        return self.request('GET', f'books/{book_id}', timeout=timeout)

    def download_book(self, book_id: int, timeout: float | None = None) -> Any:
        return self.request('GET', f'books/{book_id}/download', timeout=timeout)

    def get_libraries(self, timeout: float | None = None) -> Any:
        return self.request('GET', 'libraries', timeout=timeout)

    def get_library(self, library_id: int, timeout: float | None = None) -> Any:
        return self.request('GET', f'libraries/{library_id}', timeout=timeout)

    def build_scan_libraries(self) -> RequestSpec:
        return self.build_request('POST', 'libraries/scan')

    def scan_libraries(self, timeout: float | None = None) -> Any:
        spec = self.build_scan_libraries()
        return self.request(spec.method, spec.path, timeout=timeout)

    def build_refresh_library(self, library_id: int) -> RequestSpec:
        return self.build_request('PUT', f'libraries/{library_id}/refresh')

    def refresh_library(self, library_id: int, timeout: float | None = None) -> Any:
        spec = self.build_refresh_library(library_id)
        return self.request(spec.method, spec.path, timeout=timeout)

    def get_authors(self, page: int = 0, size: int = 20, timeout: float | None = None) -> Any:
        return self.request('GET', 'authors', params={'page': page, 'size': size}, timeout=timeout)

    def get_author(self, author_id: int, timeout: float | None = None) -> Any:
        return self.request('GET', f'authors/{author_id}', timeout=timeout)

    def get_shelves(self, timeout: float | None = None) -> Any:
        return self.request('GET', 'shelves', timeout=timeout)

    def get_shelf_books(self, shelf_id: int, timeout: float | None = None) -> Any:
        return self.request('GET', f'shelves/{shelf_id}/books', timeout=timeout)

    def get_tasks(self, timeout: float | None = None) -> Any:
        return self.request('GET', 'tasks', timeout=timeout)

    def build_cancel_task(self, task_id: str) -> RequestSpec:
        return self.build_request('DELETE', f'tasks/{task_id}/cancel')

    def cancel_task(self, task_id: str, timeout: float | None = None) -> Any:
        spec = self.build_cancel_task(task_id)
        return self.request(spec.method, spec.path, timeout=timeout)

    def get_version(self, timeout: float | None = None) -> Any:
        return self.request('GET', 'version', timeout=timeout)
