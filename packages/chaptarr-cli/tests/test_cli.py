from __future__ import annotations

import json

from typer.testing import CliRunner

from ghostship_cli_contract import RequestSpec
from ghostship_chaptarr import cli

runner = CliRunner()


class DummyClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, object]] = []

    def normalize_path(self, path: str) -> str:
        return path

    def build_request(self, method: str, path: str, *, query_params=None, json_body=None, timeout=None):
        self.calls.append(('build_request', path, method, query_params, json_body, timeout))
        return RequestSpec(method=method, path=path, params=query_params, json_body=json_body, timeout=timeout)

    def request_json(self, method: str, path: str, *, params=None, json_body=None, timeout=None) -> dict[str, object]:
        self.calls.append(('request_json', path, method, params, json_body, timeout))
        return {'method': method, 'path': path, 'timeout': timeout}

    def build_operation_request(self, command_name: str, **kwargs):
        self.calls.append(('build_operation', command_name, kwargs))
        return RequestSpec(method='POST', path='/api/v1/author', params=kwargs.get('query_params'), json_body=kwargs.get('json_body'), timeout=kwargs.get('timeout'))

    def request_operation(self, command_name: str, **kwargs):
        self.calls.append(('request_operation', command_name, kwargs))
        return {'command': command_name, 'timeout': kwargs.get('timeout')}


def test_request_dry_run_emits_spec(monkeypatch) -> None:
    client = DummyClient()
    monkeypatch.setattr(cli, 'get_client', lambda: client)
    result = runner.invoke(cli.app, ['request', 'GET', '/api/v1/system/status', '--dry-run'])
    assert result.exit_code == 0
    expected = json.loads(result.stdout)
    assert expected['method'] == 'GET'
    assert expected['path'] == '/api/v1/system/status'


def test_operation_command_dry_run(monkeypatch) -> None:
    client = DummyClient()
    monkeypatch.setattr(cli, 'get_client', lambda: client)
    result = runner.invoke(cli.app, ['post_api_v1_author', '--body-json', '{}', '--dry-run'])
    assert result.exit_code == 0
    parsed = json.loads(result.stdout)
    assert parsed['method'] == 'POST'
    assert parsed['path'] == '/api/v1/author'
    assert client.calls[0][0] == 'build_operation'
