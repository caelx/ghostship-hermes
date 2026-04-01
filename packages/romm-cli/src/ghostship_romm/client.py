from __future__ import annotations

from typing import Any

from ghostship_cli_contract import BaseHttpClient, ConfigError, RequestSpec


class RommClient(BaseHttpClient):
    def __init__(self, base_url: str, token: str | None = None, username: str | None = None, password: str | None = None, *, default_timeout: float = 30.0):
        base = base_url.rstrip('/')
        if '/api' not in base:
            base = f'{base}/api'
        resolved_token = token or self._authenticate(base, username=username, password=password, timeout=default_timeout)
        if not resolved_token:
            raise ConfigError('RomM authentication requires a token or username/password.')
        super().__init__(base, default_headers={'Authorization': f'Bearer {resolved_token}'}, default_timeout=default_timeout)

    @staticmethod
    def _authenticate(api_base_url: str, *, username: str | None, password: str | None, timeout: float) -> str:
        if not username or not password:
            raise ConfigError('Set ROMM_TOKEN or ROMM_USERNAME and ROMM_PASSWORD to authenticate.')
        payload = BaseHttpClient(api_base_url, default_timeout=timeout).request_json('POST', '/token', form_data={'grant_type': 'password', 'username': username, 'password': password}, timeout=timeout)
        token = payload.get('access_token')
        if not token:
            raise ConfigError('RomM /api/token response did not include access_token.')
        return str(token)

    def build_request(self, method: str, path: str, *, params: dict[str, Any] | None = None, json_data: dict[str, Any] | list[Any] | None = None, timeout: float | None = None) -> RequestSpec:
        return self.build_request_spec(method, path, params=params, json_body=json_data, timeout=timeout)

    def request(self, method: str, path: str, *, params: dict[str, Any] | None = None, json_data: dict[str, Any] | list[Any] | None = None, timeout: float | None = None) -> Any:
        spec = self.build_request(method, path, params=params, json_data=json_data, timeout=timeout)
        return self.request_json(spec.method, spec.path, params=spec.params, json_body=spec.json_body, timeout=spec.timeout)

    def get_heartbeat(self, timeout: float | None = None) -> Any:
        return self.request('GET', 'heartbeat', timeout=timeout)

    def get_platforms(self, timeout: float | None = None) -> Any:
        return self.request('GET', 'platforms', timeout=timeout)

    def get_libraries(self, timeout: float | None = None) -> Any:
        return self.request('GET', 'libraries', timeout=timeout)

    def get_roms(self, page: int = 1, page_size: int = 24, platform: str | None = None, timeout: float | None = None) -> Any:
        params = {'page': page, 'page_size': page_size}
        if platform:
            params['platform'] = platform
        return self.request('GET', 'roms', params=params, timeout=timeout)

    def get_rom(self, rom_id: int, timeout: float | None = None) -> Any:
        return self.request('GET', f'roms/{rom_id}', timeout=timeout)

    def build_update_rom(self, rom_id: int, data: dict[str, Any]) -> RequestSpec:
        return self.build_request('PUT', f'roms/{rom_id}', json_data=data)

    def update_rom(self, rom_id: int, data: dict[str, Any], timeout: float | None = None) -> Any:
        spec = self.build_update_rom(rom_id, data)
        return self.request(spec.method, spec.path, json_data=spec.json_body, timeout=timeout)

    def build_delete_rom(self, rom_id: int) -> RequestSpec:
        return self.build_request('DELETE', f'roms/{rom_id}')

    def delete_rom(self, rom_id: int, timeout: float | None = None) -> Any:
        spec = self.build_delete_rom(rom_id)
        return self.request(spec.method, spec.path, timeout=timeout)

    def get_scans(self, timeout: float | None = None) -> Any:
        return self.request('GET', 'scans', timeout=timeout)

    def build_start_scan(self, library_id: int | None = None) -> RequestSpec:
        path = 'scans' if library_id is None else f'scans/{library_id}'
        return self.build_request('POST', path)

    def start_scan(self, library_id: int | None = None, timeout: float | None = None) -> Any:
        spec = self.build_start_scan(library_id)
        return self.request(spec.method, spec.path, timeout=timeout)

    def get_collections(self, timeout: float | None = None) -> Any:
        return self.request('GET', 'collections', timeout=timeout)

    def get_config(self, timeout: float | None = None) -> Any:
        return self.request('GET', 'config', timeout=timeout)

    def get_saves(self, page: int = 1, page_size: int = 24, timeout: float | None = None) -> Any:
        return self.request('GET', 'saves', params={'page': page, 'page_size': page_size}, timeout=timeout)

    def get_saves_summary(self, timeout: float | None = None) -> Any:
        return self.request('GET', 'saves/summary', timeout=timeout)

    def get_save(self, save_id: int, timeout: float | None = None) -> Any:
        return self.request('GET', f'saves/{save_id}', timeout=timeout)

    def get_users(self, timeout: float | None = None) -> Any:
        return self.request('GET', 'users', timeout=timeout)

    def get_user_me(self, timeout: float | None = None) -> Any:
        return self.request('GET', 'users/me', timeout=timeout)
