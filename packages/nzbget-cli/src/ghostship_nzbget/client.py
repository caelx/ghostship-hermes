from __future__ import annotations

from typing import Any

import httpx

from ghostship_cli_contract import BaseHttpClient, HttpStatusError, RequestSpec


class NZBGetClient(BaseHttpClient):
    def __init__(self, base_url: str, username: str | None = None, password: str | None = None, *, default_timeout: float = 30.0):
        base = base_url.rstrip('/')
        if not base.endswith('/jsonrpc'):
            base = f'{base}/jsonrpc'
        super().__init__(base, default_timeout=default_timeout)
        self.auth = (username, password) if username and password else None

    def _client(self, timeout: float) -> httpx.Client:
        return httpx.Client(headers=self.default_headers, timeout=timeout, auth=self.auth, transport=self.transport, follow_redirects=self.follow_redirects)

    def build_call(self, method: str, params: list[Any] | None = None) -> RequestSpec:
        return self.build_request_spec('POST', '', json_body={'version': '1.1', 'method': method, 'params': params or []})

    def call(self, method: str, params: list[Any] | None = None, timeout: float | None = None) -> Any:
        spec = self.build_call(method, params=params)
        payload = self.request_json(spec.method, spec.path, json_body=spec.json_body, timeout=timeout if timeout is not None else spec.timeout)
        if payload.get('error'):
            raise HttpStatusError('remote service returned API error', status_code=200, details=payload['error'])
        return payload.get('result')

    def get_version(self, timeout: float | None = None) -> str:
        return self.call('version', timeout=timeout)

    def build_shutdown(self) -> RequestSpec:
        return self.build_call('shutdown')

    def shutdown(self, timeout: float | None = None) -> bool:
        return self.call('shutdown', timeout=timeout)

    def build_reload(self) -> RequestSpec:
        return self.build_call('reload')

    def reload(self, timeout: float | None = None) -> bool:
        return self.call('reload', timeout=timeout)

    def get_status(self, timeout: float | None = None) -> Any:
        return self.call('status', timeout=timeout)

    def list_groups(self, timeout: float | None = None) -> Any:
        return self.call('listgroups', timeout=timeout)

    def list_files(self, nzb_id: int, timeout: float | None = None) -> Any:
        return self.call('listfiles', [0, 0, nzb_id], timeout=timeout)

    def get_history(self, timeout: float | None = None) -> Any:
        return self.call('history', timeout=timeout)

    def build_append_url(self, url: str, category: str = '', priority: int = 0, top: bool = False) -> RequestSpec:
        return self.build_call('append', [url, '', category, priority, top, False, '', 0, 'SCORE'])

    def append_url(self, url: str, category: str = '', priority: int = 0, top: bool = False, timeout: float | None = None) -> int:
        return self.call('append', [url, '', category, priority, top, False, '', 0, 'SCORE'], timeout=timeout)

    def build_edit_queue(self, command: str, offset: int, size: int, ids: list[int]) -> RequestSpec:
        return self.build_call('editqueue', [command, offset, size, ids])

    def edit_queue(self, command: str, offset: int, size: int, ids: list[int], timeout: float | None = None) -> bool:
        return self.call('editqueue', [command, offset, size, ids], timeout=timeout)

    def build_disk_scan(self) -> RequestSpec:
        return self.build_call('scan')

    def disk_scan(self, timeout: float | None = None) -> bool:
        return self.call('scan', timeout=timeout)

    def get_log(self, id_from: int, count: int, timeout: float | None = None) -> Any:
        return self.call('log', [id_from, count], timeout=timeout)

    def build_set_rate(self, limit_kb: int) -> RequestSpec:
        return self.build_call('rate', [limit_kb])

    def set_rate(self, limit_kb: int, timeout: float | None = None) -> bool:
        return self.call('rate', [limit_kb], timeout=timeout)

    def build_pause_download(self) -> RequestSpec:
        return self.build_call('pausedownload')

    def pause_download(self, timeout: float | None = None) -> bool:
        return self.call('pausedownload', timeout=timeout)

    def build_resume_download(self) -> RequestSpec:
        return self.build_call('resumedownload')

    def resume_download(self, timeout: float | None = None) -> bool:
        return self.call('resumedownload', timeout=timeout)

    def build_pause_post(self) -> RequestSpec:
        return self.build_call('pausepost')

    def pause_post(self, timeout: float | None = None) -> bool:
        return self.call('pausepost', timeout=timeout)

    def build_resume_post(self) -> RequestSpec:
        return self.build_call('resumepost')

    def resume_post(self, timeout: float | None = None) -> bool:
        return self.call('resumepost', timeout=timeout)

    def build_pause_scan(self) -> RequestSpec:
        return self.build_call('pausescan')

    def pause_scan(self, timeout: float | None = None) -> bool:
        return self.call('pausescan', timeout=timeout)

    def build_resume_scan(self) -> RequestSpec:
        return self.build_call('resumescan')

    def resume_scan(self, timeout: float | None = None) -> bool:
        return self.call('resumescan', timeout=timeout)

    def get_config(self, timeout: float | None = None) -> Any:
        return self.call('config', timeout=timeout)

    def build_save_config(self, config: list[dict[str, str]]) -> RequestSpec:
        return self.build_call('saveconfig', [config])

    def save_config(self, config: list[dict[str, str]], timeout: float | None = None) -> bool:
        return self.call('saveconfig', [config], timeout=timeout)
