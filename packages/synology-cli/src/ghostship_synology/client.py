from __future__ import annotations

from pathlib import Path
from typing import Any

import httpx

from ghostship_cli_contract import BaseHttpClient, HttpStatusError, RequestSpec


class SynologyClient(BaseHttpClient):
    def __init__(
        self,
        base_url: str,
        username: str,
        password: str,
        verify_ssl: bool = True,
        *,
        default_timeout: float = 30.0,
        transport: httpx.BaseTransport | None = None,
    ):
        super().__init__(base_url, default_timeout=default_timeout, transport=transport)
        self.username = username
        self.password = password
        self.verify_ssl = verify_ssl
        self.sid: str | None = None
        self.api_info: dict[str, Any] = {}

    def _client(self, timeout: float) -> httpx.Client:
        return httpx.Client(
            headers=self.default_headers,
            timeout=timeout,
            transport=self.transport,
            follow_redirects=self.follow_redirects,
            verify=self.verify_ssl,
        )

    def build_call(
        self,
        api: str,
        method_name: str,
        *,
        version: int | None = None,
        path: str | None = None,
        params: dict[str, Any] | None = None,
        http_method: str | None = None,
        files: dict[str, Any] | list[Any] | None = None,
        use_sid: bool = True,
        timeout: float | None = None,
    ) -> RequestSpec:
        info = self.api_info.get(api, {})
        resolved_version = version if version is not None else info.get('maxVersion', 1)
        resolved_path = path if path is not None else info.get('path', 'entry.cgi')
        query_params: dict[str, Any] = {
            'api': api,
            'version': resolved_version,
            'method': method_name,
        }
        if params:
            query_params.update(params)
        if use_sid and self.sid and api != 'SYNO.API.Auth':
            query_params['_sid'] = self.sid
        transport_method = (http_method or ('POST' if files else 'GET')).upper()
        return self.build_request_spec(
            transport_method,
            f'/webapi/{resolved_path}',
            params=query_params,
            files=files,
            timeout=timeout,
        )

    def call(
        self,
        api: str,
        method_name: str,
        *,
        version: int | None = None,
        path: str | None = None,
        params: dict[str, Any] | None = None,
        http_method: str | None = None,
        files: dict[str, Any] | list[Any] | None = None,
        use_sid: bool = True,
        timeout: float | None = None,
    ) -> Any:
        spec = self.build_call(
            api,
            method_name,
            version=version,
            path=path,
            params=params,
            http_method=http_method,
            files=files,
            use_sid=use_sid,
            timeout=timeout,
        )
        response = BaseHttpClient.request(self, spec)
        data = response.json()
        if not data.get('success'):
            raise HttpStatusError(
                'remote service returned Synology API error',
                status_code=response.status_code,
                details=data,
            )
        return data.get('data')

    def get_info(self, query: str = 'all', *, timeout: float | None = None) -> Any:
        data = self.call('SYNO.API.Info', 'query', version=1, path='query.cgi', params={'query': query}, use_sid=False, timeout=timeout)
        self.api_info.update(data)
        return data

    def build_login(self, *, timeout: float | None = None) -> RequestSpec:
        auth_info = self.api_info.get('SYNO.API.Auth', {})
        return self.build_call(
            'SYNO.API.Auth',
            'login',
            version=auth_info.get('maxVersion', 6),
            path=auth_info.get('path', 'auth.cgi'),
            params={
                'account': self.username,
                'passwd': self.password,
                'session': 'FileStation',
                'format': 'sid',
            },
            use_sid=False,
            timeout=timeout,
        )

    def login(self, *, timeout: float | None = None) -> str:
        if not self.api_info:
            self.get_info(timeout=timeout)
        data = self.call(
            'SYNO.API.Auth',
            'login',
            version=self.api_info.get('SYNO.API.Auth', {}).get('maxVersion', 6),
            path=self.api_info.get('SYNO.API.Auth', {}).get('path', 'auth.cgi'),
            params={
                'account': self.username,
                'passwd': self.password,
                'session': 'FileStation',
                'format': 'sid',
            },
            use_sid=False,
            timeout=timeout,
        )
        self.sid = data.get('sid')
        return self.sid or ''

    def build_logout(self, *, timeout: float | None = None) -> RequestSpec:
        auth_info = self.api_info.get('SYNO.API.Auth', {})
        return self.build_call(
            'SYNO.API.Auth',
            'logout',
            version=auth_info.get('maxVersion', 6),
            path=auth_info.get('path', 'auth.cgi'),
            params={'session': 'FileStation'},
            use_sid=False,
            timeout=timeout,
        )

    def logout(self, *, timeout: float | None = None) -> bool:
        if not self.sid:
            return True
        auth_info = self.api_info.get('SYNO.API.Auth', {})
        self.call(
            'SYNO.API.Auth',
            'logout',
            version=auth_info.get('maxVersion', 6),
            path=auth_info.get('path', 'auth.cgi'),
            params={'session': 'FileStation'},
            use_sid=False,
            timeout=timeout,
        )
        self.sid = None
        return True

    def list_shares(self, *, timeout: float | None = None) -> Any:
        return self.call('SYNO.FileStation.List', 'list_share', timeout=timeout)

    def list_files(self, folder_path: str, offset: int = 0, limit: int = 100, sort_by: str = 'name', *, timeout: float | None = None) -> Any:
        return self.call(
            'SYNO.FileStation.List',
            'list',
            params={'folder_path': folder_path, 'offset': offset, 'limit': limit, 'sort_by': sort_by},
            timeout=timeout,
        )

    def get_file_info(self, path: str, *, timeout: float | None = None) -> Any:
        return self.call('SYNO.FileStation.List', 'getinfo', params={'path': path}, timeout=timeout)

    def build_search_start(self, folder_path: str, pattern: str, recursive: bool = True, *, timeout: float | None = None) -> RequestSpec:
        return self.build_call(
            'SYNO.FileStation.Search',
            'start',
            params={'folder_path': folder_path, 'pattern': pattern, 'recursive': str(recursive).lower()},
            timeout=timeout,
        )

    def search_start(self, folder_path: str, pattern: str, recursive: bool = True, *, timeout: float | None = None) -> str:
        data = self.call(
            'SYNO.FileStation.Search',
            'start',
            params={'folder_path': folder_path, 'pattern': pattern, 'recursive': str(recursive).lower()},
            timeout=timeout,
        )
        return data.get('taskid', '')

    def search_list(self, taskid: str, offset: int = 0, limit: int = 100, *, timeout: float | None = None) -> Any:
        return self.call('SYNO.FileStation.Search', 'list', params={'taskid': taskid, 'offset': offset, 'limit': limit}, timeout=timeout)

    def build_create_folder(self, folder_path: str, name: str, force_parent: bool = False, *, timeout: float | None = None) -> RequestSpec:
        return self.build_call(
            'SYNO.FileStation.CreateFolder',
            'create',
            params={'folder_path': folder_path, 'name': name, 'force_parent': str(force_parent).lower()},
            timeout=timeout,
        )

    def create_folder(self, folder_path: str, name: str, force_parent: bool = False, *, timeout: float | None = None) -> Any:
        return self.call(
            'SYNO.FileStation.CreateFolder',
            'create',
            params={'folder_path': folder_path, 'name': name, 'force_parent': str(force_parent).lower()},
            timeout=timeout,
        )

    def build_rename(self, path: str, name: str, *, timeout: float | None = None) -> RequestSpec:
        return self.build_call('SYNO.FileStation.Rename', 'rename', params={'path': path, 'name': name}, timeout=timeout)

    def rename(self, path: str, name: str, *, timeout: float | None = None) -> Any:
        return self.call('SYNO.FileStation.Rename', 'rename', params={'path': path, 'name': name}, timeout=timeout)

    def build_delete(self, path: str, recursive: bool = True, *, timeout: float | None = None) -> RequestSpec:
        return self.build_call(
            'SYNO.FileStation.Delete',
            'start',
            params={'path': path, 'recursive': str(recursive).lower()},
            timeout=timeout,
        )

    def delete(self, path: str, recursive: bool = True, *, timeout: float | None = None) -> str:
        data = self.call(
            'SYNO.FileStation.Delete',
            'start',
            params={'path': path, 'recursive': str(recursive).lower()},
            timeout=timeout,
        )
        return data.get('taskid', '')

    def download_file(self, path: str, mode: str = 'download', *, timeout: float | None = None) -> httpx.Response:
        spec = self.build_call('SYNO.FileStation.Download', 'download', params={'path': path, 'mode': mode}, timeout=timeout)
        return BaseHttpClient.request(self, spec)

    def build_upload_file(self, folder_path: str, file_path: str, create_parents: bool = True, *, timeout: float | None = None) -> RequestSpec:
        filename = Path(file_path).name
        info = self.api_info.get('SYNO.FileStation.Upload', {})
        return self.build_call(
            'SYNO.FileStation.Upload',
            'upload',
            version=info.get('maxVersion', 2),
            path=info.get('path', 'entry.cgi'),
            params={'path': folder_path, 'create_parents': str(create_parents).lower()},
            http_method='POST',
            files={'file': (filename, b'', 'application/octet-stream')},
            timeout=timeout,
        )

    def upload_file(self, folder_path: str, file_path: str, create_parents: bool = True, *, timeout: float | None = None) -> Any:
        info = self.api_info.get('SYNO.FileStation.Upload', {})
        with open(file_path, 'rb') as handle:
            return self.call(
                'SYNO.FileStation.Upload',
                'upload',
                version=info.get('maxVersion', 2),
                path=info.get('path', 'entry.cgi'),
                params={'path': folder_path, 'create_parents': str(create_parents).lower()},
                http_method='POST',
                files={'file': (Path(file_path).name, handle)},
                timeout=timeout,
            )

    def build_copy(self, path: str, destination: str, overwrite: bool = True, *, timeout: float | None = None) -> RequestSpec:
        return self.build_call(
            'SYNO.FileStation.CopyMove',
            'copy',
            params={'path': path, 'destination': destination, 'overwrite': str(overwrite).lower()},
            http_method='POST',
            timeout=timeout,
        )

    def copy(self, path: str, destination: str, overwrite: bool = True, *, timeout: float | None = None) -> Any:
        return self.call(
            'SYNO.FileStation.CopyMove',
            'copy',
            params={'path': path, 'destination': destination, 'overwrite': str(overwrite).lower()},
            http_method='POST',
            timeout=timeout,
        )

    def build_move(self, path: str, destination: str, overwrite: bool = True, *, timeout: float | None = None) -> RequestSpec:
        return self.build_call(
            'SYNO.FileStation.CopyMove',
            'move',
            params={'path': path, 'destination': destination, 'overwrite': str(overwrite).lower()},
            http_method='POST',
            timeout=timeout,
        )

    def move(self, path: str, destination: str, overwrite: bool = True, *, timeout: float | None = None) -> Any:
        return self.call(
            'SYNO.FileStation.CopyMove',
            'move',
            params={'path': path, 'destination': destination, 'overwrite': str(overwrite).lower()},
            http_method='POST',
            timeout=timeout,
        )
