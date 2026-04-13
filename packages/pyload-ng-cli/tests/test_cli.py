from __future__ import annotations

import json
import os

from typer.testing import CliRunner

from ghostship_pyload_ng import cli


runner = CliRunner()


class DummyClient:
    def __init__(self):
        self.calls = []

    def get_server_status(self, *, timeout=None):
        self.calls.append(('get_server_status', timeout))
        return {'ok': True}

    def build_add_package(self, name, links):
        class _Spec:
            def __init__(self, payload): self.payload = payload
            def to_dict(self): return self.payload
        return _Spec({'json_body': {'name': name, 'links': links}})

    def add_package(self, name, links, *, timeout=None):
        self.calls.append(('add_package', name, links, timeout))
        return {'ok': True}


def test_get_client_reads_api_key(monkeypatch):
    monkeypatch.setenv('PYLOAD_URL', 'https://pyload.example')
    monkeypatch.setenv('PYLOAD_API_KEY', 'pl_demo')
    client = cli.get_client()
    assert client.base_url == 'https://pyload.example'
    assert client.default_headers['X-API-Key'] == 'pl_demo'


def test_timeout_applies(monkeypatch):
    client = DummyClient()
    monkeypatch.setattr(cli, 'get_client', lambda: client)
    result = runner.invoke(cli.app, ['--timeout', '8', 'get_server_status'])
    assert result.exit_code == 0
    assert client.calls[-1] == ('get_server_status', 8.0)


def test_add_package_dry_run(monkeypatch):
    client = DummyClient()
    monkeypatch.setattr(cli, 'get_client', lambda: client)
    result = runner.invoke(cli.app, ['add_package', 'demo', '--links-json', '["https://example.com"]', '--dry-run'])
    assert result.exit_code == 0
    assert 'https://example.com' in result.stdout
    assert not client.calls
