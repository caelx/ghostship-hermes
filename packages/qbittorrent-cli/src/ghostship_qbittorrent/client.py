from __future__ import annotations

from typing import Any
import json

import httpx

from ghostship_cli_contract import BaseHttpClient, ConfigError, RequestSpec, TimeoutError, TransportError, HttpStatusError


class QBitClient(BaseHttpClient):
    def __init__(self, base_url: str, username: str | None = None, password: str | None = None, *, default_timeout: float = 30.0):
        base = base_url.rstrip('/')
        if '/api/v2' not in base:
            base = f'{base}/api/v2'
        super().__init__(base, default_timeout=default_timeout)
        self.username = username
        self.password = password
        self.cookies: httpx.Cookies | None = None

    def _ensure_login(self, timeout: float) -> None:
        if self.cookies is not None or not (self.username and self.password):
            return
        url = f'{self.base_url}/auth/login'
        try:
            with httpx.Client(headers=self.default_headers, timeout=timeout) as client:
                response = client.post(url, data={'username': self.username, 'password': self.password})
        except httpx.TimeoutException as exc:
            raise TimeoutError(f'request timed out after {timeout} seconds', details={'method': 'POST', 'path': '/auth/login', 'timeout': timeout}) from exc
        except httpx.HTTPError as exc:
            raise TransportError(str(exc), details={'method': 'POST', 'path': '/auth/login'}) from exc
        if response.is_error:
            raise HttpStatusError(f'remote service returned HTTP {response.status_code}', status_code=response.status_code, details=response.text or None)
        if response.text != 'Ok.':
            raise ConfigError('qBittorrent login failed with the supplied credentials.')
        self.cookies = response.cookies

    def _client(self, timeout: float) -> httpx.Client:
        self._ensure_login(timeout)
        return httpx.Client(headers=self.default_headers, timeout=timeout, cookies=self.cookies, transport=self.transport, follow_redirects=self.follow_redirects)

    def build_request(self, method: str, path: str, *, params: dict[str, Any] | None = None, data: dict[str, Any] | None = None, json_data: dict[str, Any] | list[Any] | None = None, timeout: float | None = None) -> RequestSpec:
        return self.build_request_spec(method, path, params=params, form_data=data, json_body=json_data, timeout=timeout)

    def request(self, method: str, path: str, *, params: dict[str, Any] | None = None, data: dict[str, Any] | None = None, json_data: dict[str, Any] | list[Any] | None = None, timeout: float | None = None) -> Any:
        spec = self.build_request(method, path, params=params, data=data, json_data=json_data, timeout=timeout)
        response = BaseHttpClient.request(self, spec)
        if not response.content:
            return {'status': 'success'}
        try:
            return response.json()
        except ValueError:
            return response.text

    def build_login(self) -> RequestSpec:
        return self.build_request('POST', 'auth/login', data={'username': self.username, 'password': self.password})

    def login(self, timeout: float | None = None) -> bool:
        self._ensure_login(timeout or self.default_timeout)
        return True

    def build_logout(self) -> RequestSpec:
        return self.build_request('POST', 'auth/logout')

    def logout(self, timeout: float | None = None) -> bool:
        if not (self.username and self.password):
            return True
        result = self.request('POST', 'auth/logout', timeout=timeout)
        return result == 'Ok.' or result.get('status') == 'success'

    def get_app_version(self, timeout: float | None = None) -> str:
        return self.request('GET', 'app/version', timeout=timeout)

    def get_api_version(self, timeout: float | None = None) -> str:
        return self.request('GET', 'app/webapiVersion', timeout=timeout)

    def build_shutdown(self) -> RequestSpec:
        return self.build_request('POST', 'app/shutdown')

    def shutdown(self, timeout: float | None = None) -> bool:
        return self.request('POST', 'app/shutdown', timeout=timeout) == 'Ok.'

    def get_preferences(self, timeout: float | None = None) -> Any:
        return self.request('GET', 'app/preferences', timeout=timeout)

    def build_set_preferences(self, prefs: dict[str, Any]) -> RequestSpec:
        return self.build_request('POST', 'app/setPreferences', data={'json': json.dumps(prefs)})

    def set_preferences(self, prefs: dict[str, Any], timeout: float | None = None) -> bool:
        return self.request('POST', 'app/setPreferences', data={'json': json.dumps(prefs)}, timeout=timeout) == 'Ok.'

    def get_log(self, last_known_id: int = -1, timeout: float | None = None) -> Any:
        return self.request('GET', 'log/main', params={'last_id': last_known_id}, timeout=timeout)

    def get_main_data(self, rid: int = 0, timeout: float | None = None) -> Any:
        return self.request('GET', 'sync/maindata', params={'rid': rid}, timeout=timeout)

    def get_transfer_info(self, timeout: float | None = None) -> Any:
        return self.request('GET', 'transfer/info', timeout=timeout)

    def get_speed_limits_mode(self, timeout: float | None = None) -> int:
        return int(self.request('GET', 'transfer/speedLimitsMode', timeout=timeout))

    def build_toggle_speed_limits_mode(self) -> RequestSpec:
        return self.build_request('POST', 'transfer/toggleSpeedLimitsMode')

    def toggle_speed_limits_mode(self, timeout: float | None = None) -> bool:
        return self.request('POST', 'transfer/toggleSpeedLimitsMode', timeout=timeout) == 'Ok.'

    def get_torrents(self, filter_type: str | None = None, category: str | None = None, sort: str | None = None, reverse: bool = False, timeout: float | None = None) -> Any:
        params = {}
        if filter_type:
            params['filter'] = filter_type
        if category:
            params['category'] = category
        if sort:
            params['sort'] = sort
        if reverse:
            params['reverse'] = str(reverse).lower()
        return self.request('GET', 'torrents/info', params=params or None, timeout=timeout)

    def build_add_torrent(self, urls: list[str], save_path: str | None = None, category: str | None = None) -> RequestSpec:
        data = {'urls': '\n'.join(urls)}
        if save_path:
            data['savepath'] = save_path
        if category:
            data['category'] = category
        return self.build_request('POST', 'torrents/add', data=data)

    def add_torrent(self, urls: list[str], save_path: str | None = None, category: str | None = None, timeout: float | None = None) -> bool:
        spec = self.build_add_torrent(urls, save_path=save_path, category=category)
        return self.request(spec.method, spec.path, data=spec.form_data, timeout=timeout) == 'Ok.'

    def build_delete_torrents(self, hashes: list[str], delete_files: bool = False) -> RequestSpec:
        return self.build_request('POST', 'torrents/delete', data={'hashes': '|'.join(hashes), 'deleteFiles': str(delete_files).lower()})

    def delete_torrents(self, hashes: list[str], delete_files: bool = False, timeout: float | None = None) -> bool:
        spec = self.build_delete_torrents(hashes, delete_files=delete_files)
        return self.request(spec.method, spec.path, data=spec.form_data, timeout=timeout) == 'Ok.'

    def build_pause_torrents(self, hashes: list[str]) -> RequestSpec:
        return self.build_request('POST', 'torrents/pause', data={'hashes': '|'.join(hashes)})

    def pause_torrents(self, hashes: list[str], timeout: float | None = None) -> bool:
        spec = self.build_pause_torrents(hashes)
        return self.request(spec.method, spec.path, data=spec.form_data, timeout=timeout) == 'Ok.'

    def build_resume_torrents(self, hashes: list[str]) -> RequestSpec:
        return self.build_request('POST', 'torrents/resume', data={'hashes': '|'.join(hashes)})

    def resume_torrents(self, hashes: list[str], timeout: float | None = None) -> bool:
        spec = self.build_resume_torrents(hashes)
        return self.request(spec.method, spec.path, data=spec.form_data, timeout=timeout) == 'Ok.'

    def build_search_start(self, pattern: str, category: str = 'all', plugins: str = 'all') -> RequestSpec:
        return self.build_request('POST', 'search/start', data={'pattern': pattern, 'category': category, 'plugins': plugins})

    def search_start(self, pattern: str, category: str = 'all', plugins: str = 'all', timeout: float | None = None) -> Any:
        spec = self.build_search_start(pattern, category=category, plugins=plugins)
        return self.request(spec.method, spec.path, data=spec.form_data, timeout=timeout)

    def search_status(self, search_id: int | None = None, timeout: float | None = None) -> Any:
        params = {'id': search_id} if search_id is not None else None
        return self.request('GET', 'search/status', params=params, timeout=timeout)

    def search_results(self, search_id: int, limit: int = 10, offset: int = 0, timeout: float | None = None) -> Any:
        return self.request('GET', 'search/results', params={'id': search_id, 'limit': limit, 'offset': offset}, timeout=timeout)

    def get_rss_data(self, with_data: bool = True, timeout: float | None = None) -> Any:
        return self.request('GET', 'rss/items', params={'withData': str(with_data).lower()}, timeout=timeout)
