from __future__ import annotations

from typing import Any

import httpx

from ghostship_cli_contract import BaseHttpClient, RequestSpec


class PyLoadClient(BaseHttpClient):
    def __init__(self, base_url: str, api_key: str | None = None, *, default_timeout: float = 30.0):
        headers = {"X-API-Key": api_key} if api_key else None
        super().__init__(base_url.rstrip('/'), default_headers=headers, default_timeout=default_timeout)

    def _client(self, timeout: float) -> httpx.Client:
        return httpx.Client(headers=self.default_headers, timeout=timeout, transport=self.transport, follow_redirects=self.follow_redirects)

    def build_request(self, method: str, path: str, *, params: dict[str, Any] | None = None, json_data: dict[str, Any] | list[Any] | None = None, timeout: float | None = None) -> RequestSpec:
        return self.build_request_spec(method, path, params=params, json_body=json_data, timeout=timeout)

    def request(self, method: str, path: str, *, params: dict[str, Any] | None = None, json_data: dict[str, Any] | list[Any] | None = None, timeout: float | None = None) -> Any:
        spec = self.build_request(method, path, params=params, json_data=json_data, timeout=timeout)
        response = BaseHttpClient.request(self, spec)
        if not response.content:
            return {'status': 'success'}
        try:
            return response.json()
        except ValueError:
            return response.text

    def get_server_status(self, timeout: float | None = None) -> Any:
        return self.request('GET', 'api/status_server', timeout=timeout)

    def get_downloads(self, timeout: float | None = None) -> Any:
        return self.request('GET', 'api/status_downloads', timeout=timeout)

    def get_queue(self, timeout: float | None = None) -> Any:
        return self.request('GET', 'api/get_queue', timeout=timeout)

    def build_add_package(self, name: str, links: list[str]) -> RequestSpec:
        return self.build_request('POST', 'api/add_package', json_data={'name': name, 'links': links})

    def add_package(self, name: str, links: list[str], timeout: float | None = None) -> Any:
        spec = self.build_add_package(name, links)
        return self.request(spec.method, spec.path, json_data=spec.json_body, timeout=timeout)

    def build_add_files(self, package_id: int, links: list[str]) -> RequestSpec:
        return self.build_request('POST', 'api/add_files', json_data={'package_id': package_id, 'links': links})

    def add_files(self, package_id: int, links: list[str], timeout: float | None = None) -> Any:
        spec = self.build_add_files(package_id, links)
        return self.request(spec.method, spec.path, json_data=spec.json_body, timeout=timeout)

    def build_delete_packages(self, package_ids: list[int]) -> RequestSpec:
        return self.build_request('POST', 'api/delete_packages', json_data={'package_ids': package_ids})

    def delete_packages(self, package_ids: list[int], timeout: float | None = None) -> Any:
        spec = self.build_delete_packages(package_ids)
        return self.request(spec.method, spec.path, json_data=spec.json_body, timeout=timeout)

    def build_toggle_pause(self) -> RequestSpec:
        return self.build_request('POST', 'api/toggle_pause')

    def toggle_pause(self, timeout: float | None = None) -> Any:
        spec = self.build_toggle_pause()
        return self.request(spec.method, spec.path, timeout=timeout)

    def get_config(self, timeout: float | None = None) -> Any:
        return self.request('GET', 'api/get_config_dict', timeout=timeout)

    def build_delete_finished(self) -> RequestSpec:
        return self.build_request('POST', 'api/delete_finished')

    def delete_finished(self, timeout: float | None = None) -> Any:
        spec = self.build_delete_finished()
        return self.request(spec.method, spec.path, timeout=timeout)

    def build_restart_failed(self) -> RequestSpec:
        return self.build_request('POST', 'api/restart_failed')

    def restart_failed(self, timeout: float | None = None) -> Any:
        spec = self.build_restart_failed()
        return self.request(spec.method, spec.path, timeout=timeout)

    def build_stop_all_downloads(self) -> RequestSpec:
        return self.build_request('POST', 'api/stop_all_downloads')

    def stop_all_downloads(self, timeout: float | None = None) -> Any:
        spec = self.build_stop_all_downloads()
        return self.request(spec.method, spec.path, timeout=timeout)

    def get_accounts(self, refresh: bool = False, timeout: float | None = None) -> Any:
        return self.request('GET', 'api/get_accounts', params={'refresh': str(refresh).lower()}, timeout=timeout)

    def build_add_account(self, plugin: str, login: str, password: str) -> RequestSpec:
        return self.build_request('POST', 'api/update_account', json_data={'plugin': plugin, 'login': login, 'password': password})

    def add_account(self, plugin: str, login: str, password: str, timeout: float | None = None) -> Any:
        spec = self.build_add_account(plugin, login, password)
        return self.request(spec.method, spec.path, json_data=spec.json_body, timeout=timeout)

    def build_remove_account(self, plugin: str, login: str) -> RequestSpec:
        return self.build_request('POST', 'api/remove_account', json_data={'plugin': plugin, 'login': login})

    def remove_account(self, plugin: str, login: str, timeout: float | None = None) -> Any:
        spec = self.build_remove_account(plugin, login)
        return self.request(spec.method, spec.path, json_data=spec.json_body, timeout=timeout)

    def get_server_version(self, timeout: float | None = None) -> Any:
        return self.request('GET', 'api/get_server_version', timeout=timeout)

    def get_free_space(self, timeout: float | None = None) -> Any:
        return self.request('GET', 'api/free_space', timeout=timeout)
