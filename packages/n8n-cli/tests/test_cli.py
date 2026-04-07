from __future__ import annotations

import json

from typer.testing import CliRunner

from ghostship_n8n import cli
from ghostship_n8n.catalog import OPERATIONS


runner = CliRunner()


class DummyClient:
    def __init__(self) -> None:
        self.calls: list[tuple] = []

    def build_operation_request(self, command_name, *, path_params=None, query_params=None, json_body=None, timeout=None):
        class _Spec:
            def __init__(self, payload):
                self.payload = payload

            def to_dict(self):
                return self.payload

        return _Spec(
            {
                'command_name': command_name,
                'path_params': path_params,
                'query_params': query_params,
                'json_body': json_body,
                'timeout': timeout,
            }
        )

    def request_operation(self, command_name, *, path_params=None, query_params=None, json_body=None, timeout=None):
        self.calls.append((command_name, path_params, query_params, json_body, timeout))
        return {'ok': True, 'command_name': command_name}

    def build_request(self, method, path, *, query_params=None, json_body=None, timeout=None):
        class _Spec:
            def __init__(self, payload):
                self.payload = payload

            def to_dict(self):
                return self.payload

        return _Spec({'method': method, 'path': path, 'query_params': query_params, 'json_body': json_body, 'timeout': timeout})

    def request_json(self, method, path, *, params=None, json_body=None, timeout=None):
        self.calls.append(('request', method, path, params, json_body, timeout))
        return {'ok': True}


def test_timeout_applies(monkeypatch):
    client = DummyClient()
    monkeypatch.setattr(cli, 'get_client', lambda: client)
    result = runner.invoke(cli.app, ['--timeout', '9', 'get_workflows'])
    assert result.exit_code == 0
    assert client.calls[-1] == ('get_workflows', None, None, None, 9.0)


def test_mutation_dry_run(monkeypatch):
    client = DummyClient()
    monkeypatch.setattr(cli, 'get_client', lambda: client)
    result = runner.invoke(
        cli.app,
        ['create_tag', '--body-json', '{"name":"Production"}', '--dry-run'],
    )
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload['command_name'] == 'create_tag'
    assert payload['json_body']['name'] == 'Production'
    assert not client.calls


def test_read_command_rejects_dry_run(monkeypatch):
    client = DummyClient()
    monkeypatch.setattr(cli, 'get_client', lambda: client)
    result = runner.invoke(cli.app, ['get_workflows', '--dry-run'])
    assert result.exit_code != 0
    assert '--dry-run is only supported' in str(result.exception)


def test_request_command_works(monkeypatch):
    client = DummyClient()
    monkeypatch.setattr(cli, 'get_client', lambda: client)
    result = runner.invoke(cli.app, ['request', 'GET', 'discover', '--query-param', 'resource=workflow'])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload['ok'] is True


def test_cli_registers_every_catalog_command() -> None:
    registered = {command.name for command in cli.app.registered_commands}
    expected = {'request'} | {operation.command_name for operation in OPERATIONS}
    assert expected <= registered
