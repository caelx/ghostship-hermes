from __future__ import annotations

from typing import Any

from ghostship_cli_contract import BaseHttpClient, RequestSpec


class CloakBrowserClient(BaseHttpClient):
    def __init__(self, base_url: str, token: str | None = None, *, default_timeout: float = 30.0):
        headers: dict[str, str] = {}
        if token:
            headers['Authorization'] = f'Bearer {token}'
        super().__init__(base_url.rstrip('/'), default_headers=headers, default_timeout=default_timeout)

    def build_request(self, method: str, path: str, *, params: dict[str, Any] | None = None, json_data: dict[str, Any] | list[Any] | None = None, timeout: float | None = None) -> RequestSpec:
        return self.build_request_spec(method, path, params=params, json_body=json_data, timeout=timeout)

    def request(self, method: str, path: str, *, params: dict[str, Any] | None = None, json_data: dict[str, Any] | list[Any] | None = None, timeout: float | None = None) -> Any:
        spec = self.build_request(method, path, params=params, json_data=json_data, timeout=timeout)
        return self.request_json(spec.method, spec.path, params=spec.params, json_body=spec.json_body, timeout=spec.timeout)

    def get_auth_status(self, timeout: float | None = None) -> dict[str, Any]:
        return self.request('GET', '/api/auth/status', timeout=timeout)

    def auth_login(self, token: str, timeout: float | None = None) -> dict[str, Any]:
        return self.request('POST', '/api/auth/login', json_data={'token': token}, timeout=timeout)

    def auth_logout(self, timeout: float | None = None) -> dict[str, Any]:
        return self.request('POST', '/api/auth/logout', timeout=timeout)

    def get_system_status(self, timeout: float | None = None) -> dict[str, Any]:
        return self.request('GET', '/api/status', timeout=timeout)

    def list_profiles(self, timeout: float | None = None) -> list[dict[str, Any]]:
        return self.request('GET', '/api/profiles', timeout=timeout)

    def get_profile(self, profile_id: str, timeout: float | None = None) -> dict[str, Any]:
        return self.request('GET', f'/api/profiles/{profile_id}', timeout=timeout)

    def build_create_profile(self, **kwargs: Any) -> RequestSpec:
        return self.build_request('POST', '/api/profiles', json_data=_profile_payload(**kwargs))

    def create_profile(self, timeout: float | None = None, **kwargs: Any) -> dict[str, Any]:
        spec = self.build_create_profile(**kwargs)
        return self.request(spec.method, spec.path, json_data=spec.json_body, timeout=timeout)

    def build_update_profile(self, profile_id: str, **kwargs: Any) -> RequestSpec:
        return self.build_request('PUT', f'/api/profiles/{profile_id}', json_data=_profile_update_payload(**kwargs))

    def update_profile(self, profile_id: str, timeout: float | None = None, **kwargs: Any) -> dict[str, Any]:
        spec = self.build_update_profile(profile_id, **kwargs)
        return self.request(spec.method, spec.path, json_data=spec.json_body, timeout=timeout)

    def build_delete_profile(self, profile_id: str) -> RequestSpec:
        return self.build_request('DELETE', f'/api/profiles/{profile_id}')

    def delete_profile(self, profile_id: str, timeout: float | None = None) -> Any:
        spec = self.build_delete_profile(profile_id)
        return self.request(spec.method, spec.path, timeout=timeout)

    def build_launch_profile(self, profile_id: str) -> RequestSpec:
        return self.build_request('POST', f'/api/profiles/{profile_id}/launch')

    def launch_profile(self, profile_id: str, timeout: float | None = None) -> dict[str, Any]:
        spec = self.build_launch_profile(profile_id)
        return self.request(spec.method, spec.path, timeout=timeout)

    def build_stop_profile(self, profile_id: str) -> RequestSpec:
        return self.build_request('POST', f'/api/profiles/{profile_id}/stop')

    def stop_profile(self, profile_id: str, timeout: float | None = None) -> Any:
        spec = self.build_stop_profile(profile_id)
        return self.request(spec.method, spec.path, timeout=timeout)

    def get_profile_status(self, profile_id: str, timeout: float | None = None) -> dict[str, Any]:
        return self.request('GET', f'/api/profiles/{profile_id}/status', timeout=timeout)

    def get_clipboard(self, profile_id: str, timeout: float | None = None) -> dict[str, Any]:
        return self.request('GET', f'/api/profiles/{profile_id}/clipboard', timeout=timeout)

    def build_set_clipboard(self, profile_id: str, text: str) -> RequestSpec:
        return self.build_request('POST', f'/api/profiles/{profile_id}/clipboard', json_data={'text': text})

    def set_clipboard(self, profile_id: str, text: str, timeout: float | None = None) -> Any:
        spec = self.build_set_clipboard(profile_id, text)
        return self.request(spec.method, spec.path, json_data=spec.json_body, timeout=timeout)

    def get_cdp_info(self, profile_id: str, timeout: float | None = None) -> dict[str, Any]:
        return self.request('GET', f'/api/profiles/{profile_id}/cdp', timeout=timeout)


def _profile_payload(
    *,
    name: str,
    fingerprint_seed: int | None = None,
    proxy: str | None = None,
    timezone: str | None = None,
    locale: str | None = None,
    platform: str = 'windows',
    user_agent: str | None = None,
    screen_width: int = 1920,
    screen_height: int = 1080,
    gpu_vendor: str | None = None,
    gpu_renderer: str | None = None,
    hardware_concurrency: int | None = None,
    humanize: bool = False,
    human_preset: str = 'default',
    headless: bool = False,
    geoip: bool = False,
    clipboard_sync: bool = True,
    color_scheme: str | None = None,
    notes: str | None = None,
    tags: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    data: dict[str, Any] = {
        'name': name,
        'platform': platform,
        'screen_width': screen_width,
        'screen_height': screen_height,
        'humanize': humanize,
        'human_preset': human_preset,
        'headless': headless,
        'geoip': geoip,
        'clipboard_sync': clipboard_sync,
    }
    optional_values = {
        'fingerprint_seed': fingerprint_seed,
        'proxy': proxy,
        'timezone': timezone,
        'locale': locale,
        'user_agent': user_agent,
        'gpu_vendor': gpu_vendor,
        'gpu_renderer': gpu_renderer,
        'hardware_concurrency': hardware_concurrency,
        'color_scheme': color_scheme,
        'notes': notes,
        'tags': tags,
    }
    data.update({key: value for key, value in optional_values.items() if value is not None})
    return data


def _profile_update_payload(**kwargs: Any) -> dict[str, Any]:
    return {key: value for key, value in kwargs.items() if value is not None}
