from __future__ import annotations

from typing import Any

from ghostship_cli_contract import BaseHttpClient, RequestSpec


class PlexClient(BaseHttpClient):
    def __init__(self, base_url: str, token: str, *, default_timeout: float = 30.0):
        headers = {'X-Plex-Token': token, 'Accept': 'application/json'}
        super().__init__(base_url.rstrip('/'), default_headers=headers, default_timeout=default_timeout)

    def build_request(self, method: str, path: str, *, params: dict[str, Any] | None = None, json_data: dict[str, Any] | list[Any] | None = None, timeout: float | None = None) -> RequestSpec:
        return self.build_request_spec(method, path, params=params, json_body=json_data, timeout=timeout)

    def request(self, method: str, path: str, *, params: dict[str, Any] | None = None, json_data: dict[str, Any] | list[Any] | None = None, timeout: float | None = None) -> Any:
        spec = self.build_request(method, path, params=params, json_data=json_data, timeout=timeout)
        return self.request_json(spec.method, spec.path, params=spec.params, json_body=spec.json_body, timeout=spec.timeout)

    def get_identity(self, timeout: float | None = None) -> Any:
        return self.request('GET', 'identity', timeout=timeout)

    def get_server_info(self, timeout: float | None = None) -> Any:
        return self.request('GET', '', timeout=timeout)

    def get_status_sessions(self, timeout: float | None = None) -> Any:
        return self.request('GET', 'status/sessions', timeout=timeout)

    def get_activities(self, timeout: float | None = None) -> Any:
        return self.request('GET', 'activities', timeout=timeout)

    def get_library_sections(self, timeout: float | None = None) -> Any:
        return self.request('GET', 'library/sections', timeout=timeout)

    def get_library_section(self, section_id: int, timeout: float | None = None) -> Any:
        return self.request('GET', f'library/sections/{section_id}/all', timeout=timeout)

    def get_library_filters(self, section_id: int, timeout: float | None = None) -> Any:
        return self.request('GET', f'library/sections/{section_id}/filters', timeout=timeout)

    def get_library_sorts(self, section_id: int, timeout: float | None = None) -> Any:
        return self.request('GET', f'library/sections/{section_id}/sorts', timeout=timeout)

    def build_refresh_library(self, section_id: int | None = None) -> RequestSpec:
        path = 'library/sections/all/refresh' if section_id is None else f'library/sections/{section_id}/refresh'
        return self.build_request('GET', path)

    def refresh_library(self, section_id: int | None = None, timeout: float | None = None) -> Any:
        spec = self.build_refresh_library(section_id)
        return self.request(spec.method, spec.path, timeout=timeout)

    def get_metadata(self, rating_key: int, timeout: float | None = None) -> Any:
        return self.request('GET', f'library/metadata/{rating_key}', timeout=timeout)

    def get_metadata_children(self, rating_key: int, timeout: float | None = None) -> Any:
        return self.request('GET', f'library/metadata/{rating_key}/children', timeout=timeout)

    def get_playlists(self, timeout: float | None = None) -> Any:
        return self.request('GET', 'playlists', timeout=timeout)

    def get_playlist_items(self, playlist_id: int, timeout: float | None = None) -> Any:
        return self.request('GET', f'playlists/{playlist_id}/items', timeout=timeout)

    def get_collections(self, section_id: int, timeout: float | None = None) -> Any:
        return self.request('GET', f'library/sections/{section_id}/collections', timeout=timeout)

    def get_preferences(self, timeout: float | None = None) -> Any:
        return self.request('GET', ':/prefs', timeout=timeout)

    def get_butler_tasks(self, timeout: float | None = None) -> Any:
        return self.request('GET', 'butler', timeout=timeout)

    def get_statistics(self, timeout: float | None = None) -> Any:
        return self.request('GET', 'statistics/resources', params={'timespan': 6}, timeout=timeout)

    def build_terminate_session(self, session_id: int) -> RequestSpec:
        return self.build_request('PUT', f'library/terminate/{session_id}')

    def terminate_session(self, session_id: int, timeout: float | None = None) -> Any:
        spec = self.build_terminate_session(session_id)
        return self.request(spec.method, spec.path, timeout=timeout)

    def get_session(self, session_id: int, timeout: float | None = None) -> Any:
        return self.request('GET', f'sessions/{session_id}', timeout=timeout)
