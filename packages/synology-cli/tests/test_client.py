from __future__ import annotations

from ghostship_synology.client import SynologyClient


class DummySynologyClient(SynologyClient):
    def __init__(self) -> None:
        super().__init__('https://synology.example', 'user', 'pass')
        self.calls: list[tuple[str, str, dict[str, object]]] = []

    def call(self, api: str, method_name: str, *, version=None, path=None, params=None, http_method=None, files=None, use_sid=True, timeout=None):
        self.calls.append((api, method_name, {'version': version, 'path': path, 'params': params, 'http_method': http_method, 'files': files, 'use_sid': use_sid, 'timeout': timeout}))
        if api == 'SYNO.FileStation.Search' and method_name == 'start':
            return {'taskid': 'task-1'}
        if api == 'SYNO.FileStation.Delete' and method_name == 'start':
            return {'taskid': 'task-2'}
        if api == 'SYNO.API.Info':
            return {'SYNO.API.Auth': {'maxVersion': 6, 'path': 'auth.cgi'}}
        if api == 'SYNO.API.Auth' and method_name == 'login':
            return {'sid': 'sid-1'}
        return {'ok': True}


def test_wrappers_delegate_to_call() -> None:
    client = DummySynologyClient()
    client.get_info(timeout=1)
    client.login(timeout=2)
    client.logout(timeout=3)
    client.list_shares(timeout=4)
    client.create_folder('/music', 'new', force_parent=True, timeout=5)
    client.rename('/music/old', 'new', timeout=6)
    client.delete('/music/old', timeout=7)
    client.copy('/music/a', '/music/b', overwrite=False, timeout=8)
    client.move('/music/a', '/music/b', timeout=9)
    assert client.calls == [
        ('SYNO.API.Info', 'query', {'version': 1, 'path': 'query.cgi', 'params': {'query': 'all'}, 'http_method': None, 'files': None, 'use_sid': False, 'timeout': 1}),
        ('SYNO.API.Auth', 'login', {'version': 6, 'path': 'auth.cgi', 'params': {'account': 'user', 'passwd': 'pass', 'session': 'FileStation', 'format': 'sid'}, 'http_method': None, 'files': None, 'use_sid': False, 'timeout': 2}),
        ('SYNO.API.Auth', 'logout', {'version': 6, 'path': 'auth.cgi', 'params': {'session': 'FileStation'}, 'http_method': None, 'files': None, 'use_sid': False, 'timeout': 3}),
        ('SYNO.FileStation.List', 'list_share', {'version': None, 'path': None, 'params': None, 'http_method': None, 'files': None, 'use_sid': True, 'timeout': 4}),
        ('SYNO.FileStation.CreateFolder', 'create', {'version': None, 'path': None, 'params': {'folder_path': '/music', 'name': 'new', 'force_parent': 'true'}, 'http_method': None, 'files': None, 'use_sid': True, 'timeout': 5}),
        ('SYNO.FileStation.Rename', 'rename', {'version': None, 'path': None, 'params': {'path': '/music/old', 'name': 'new'}, 'http_method': None, 'files': None, 'use_sid': True, 'timeout': 6}),
        ('SYNO.FileStation.Delete', 'start', {'version': None, 'path': None, 'params': {'path': '/music/old', 'recursive': 'true'}, 'http_method': None, 'files': None, 'use_sid': True, 'timeout': 7}),
        ('SYNO.FileStation.CopyMove', 'copy', {'version': None, 'path': None, 'params': {'path': '/music/a', 'destination': '/music/b', 'overwrite': 'false'}, 'http_method': 'POST', 'files': None, 'use_sid': True, 'timeout': 8}),
        ('SYNO.FileStation.CopyMove', 'move', {'version': None, 'path': None, 'params': {'path': '/music/a', 'destination': '/music/b', 'overwrite': 'true'}, 'http_method': 'POST', 'files': None, 'use_sid': True, 'timeout': 9}),
    ]


def test_builders() -> None:
    client = SynologyClient('https://synology.example', 'user', 'pass')
    spec = client.build_create_folder('/music', 'new', force_parent=False)
    assert spec.to_dict()['params']['api'] == 'SYNO.FileStation.CreateFolder'
    assert spec.to_dict()['params']['folder_path'] == '/music'
    delete_spec = client.build_delete('/music/old')
    assert delete_spec.to_dict()['params']['method'] == 'start'
