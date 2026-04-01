from __future__ import annotations

import json

from typer.testing import CliRunner

from ghostship_synology import cli


runner = CliRunner()


class DummyClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple[object, ...], dict[str, object]]] = []
        self.sid = 'sid-1'

    def login(self, *, timeout=None):
        self.calls.append(('login', (), {'timeout': timeout}))
        return 'sid-1'

    def logout(self, *, timeout=None):
        self.calls.append(('logout', (), {'timeout': timeout}))
        return True

    def list_shares(self, *, timeout=None):
        self.calls.append(('list_shares', (), {'timeout': timeout}))
        return {'shares': []}

    def build_create_folder(self, folder_path: str, name: str, force_parent: bool = False, *, timeout=None):
        class _Spec:
            def __init__(self, payload):
                self.payload = payload
            def to_dict(self):
                return self.payload
        return _Spec({'method': 'GET', 'path': '/webapi/entry.cgi', 'params': {'api': 'SYNO.FileStation.CreateFolder', 'method': 'create', 'folder_path': folder_path, 'name': name, 'force_parent': str(force_parent).lower()}, 'timeout': timeout})

    def create_folder(self, folder_path: str, name: str, force_parent: bool = False, *, timeout=None):
        self.calls.append(('create_folder', (folder_path, name), {'force_parent': force_parent, 'timeout': timeout}))
        return {'ok': True}


def test_timeout_applies(monkeypatch):
    client = DummyClient()
    monkeypatch.setattr(cli, 'get_client', lambda: client)
    result = runner.invoke(cli.app, ['--timeout', '8', 'list_shares'])
    assert result.exit_code == 0
    assert client.calls == [
        ('login', (), {'timeout': 8.0}),
        ('list_shares', (), {'timeout': 8.0}),
        ('logout', (), {'timeout': 8.0}),
    ]


def test_create_folder_dry_run(monkeypatch):
    client = DummyClient()
    monkeypatch.setattr(cli, 'get_client', lambda: client)
    result = runner.invoke(cli.app, ['create_folder', '/music', 'new', '--dry-run'])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload['params']['api'] == 'SYNO.FileStation.CreateFolder'
    assert not client.calls
