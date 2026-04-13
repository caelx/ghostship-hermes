from __future__ import annotations

import json
from pathlib import Path

import httpx
from typer.testing import CliRunner

from ghostship_bookstack import cli
from ghostship_bookstack.catalog import OPERATIONS
from ghostship_bookstack.client import BookStackClient

runner = CliRunner()


class DummyClient:
    def __init__(self) -> None:
        self.calls: list[tuple] = []

    def build_operation_request(self, command_name, *, path_params=None, query_params=None, json_body=None, form_data=None, files=None, timeout=None):
        class _Spec:
            def __init__(self, payload):
                self.payload = payload

            def to_dict(self):
                return self.payload

        serialized_files = None
        if isinstance(files, dict):
            serialized_files = {key: {'filename': value[0], 'content_type': value[2]} for key, value in files.items()}
        return _Spec({
            'command_name': command_name,
            'path_params': path_params,
            'query_params': query_params,
            'json_body': json_body,
            'form_data': form_data,
            'files': serialized_files,
            'timeout': timeout,
        })

    def request_operation(self, command_name, *, path_params=None, query_params=None, json_body=None, form_data=None, files=None, timeout=None):
        self.calls.append((command_name, path_params, query_params, json_body, form_data, files, timeout))
        return {'ok': True, 'command_name': command_name}

    def build_request(self, method, path, *, query_params=None, json_body=None, form_data=None, files=None, timeout=None):
        class _Spec:
            def __init__(self, payload):
                self.payload = payload

            def to_dict(self):
                return self.payload

        return _Spec({'method': method, 'path': path, 'query_params': query_params, 'json_body': json_body, 'form_data': form_data, 'files': files, 'timeout': timeout})

    def request(self, method, path, *, query_params=None, json_body=None, form_data=None, files=None, timeout=None):
        self.calls.append(('request', method, path, query_params, json_body, form_data, files, timeout))
        return {'ok': True}


def test_timeout_applies(monkeypatch):
    client = DummyClient()
    monkeypatch.setattr(cli, 'get_client', lambda: client)
    result = runner.invoke(cli.app, ['--timeout', '9', 'pages_list'])
    assert result.exit_code == 0
    assert client.calls[-1] == ('pages_list', None, None, None, None, None, 9.0)


def test_multipart_dry_run(monkeypatch, tmp_path: Path):
    client = DummyClient()
    monkeypatch.setattr(cli, 'get_client', lambda: client)
    payload = tmp_path / 'cover.png'
    payload.write_bytes(b'png')
    result = runner.invoke(
        cli.app,
        ['books_create', '--form-param', 'name=Runbook', '--file', f'image={payload}', '--dry-run'],
    )
    assert result.exit_code == 0
    body = json.loads(result.stdout)
    assert body['command_name'] == 'books_create'
    assert body['form_data']['name'] == 'Runbook'
    assert body['files']['image']['filename'] == 'cover.png'
    assert not client.calls


def test_binary_command_requires_output(monkeypatch):
    client = DummyClient()
    monkeypatch.setattr(cli, 'get_client', lambda: client)
    result = runner.invoke(cli.app, ['pages_export_markdown', '--path-param', 'id=4'])
    assert result.exit_code != 0
    assert '--output is required' in result.stderr or '--output is required' in str(result.exception)


def test_cli_registers_every_catalog_command() -> None:
    registered = {command.name for command in cli.app.registered_commands}
    expected = {'request'} | {operation.command_name for operation in OPERATIONS}
    assert expected <= registered


def test_request_command_executes_against_real_client(monkeypatch) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == '/api/books'
        return httpx.Response(200, request=request, json={'data': [], 'total': 0})

    client = BookStackClient('https://bookstack.example', 'token-id', 'token-secret', transport=httpx.MockTransport(handler))
    monkeypatch.setattr(cli, 'get_client', lambda: client)

    result = runner.invoke(cli.app, ['--timeout', '30', 'request', 'GET', '/books', '--pretty'])

    assert result.exit_code == 0
    assert json.loads(result.stdout) == {'data': [], 'total': 0}


def test_docs_display_command_executes_against_real_client(monkeypatch) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == '/api/docs'
        return httpx.Response(200, request=request, text='<html>docs</html>', headers={'content-type': 'text/html; charset=utf-8'})

    client = BookStackClient('https://bookstack.example', 'token-id', 'token-secret', transport=httpx.MockTransport(handler))
    monkeypatch.setattr(cli, 'get_client', lambda: client)

    result = runner.invoke(cli.app, ['--timeout', '30', 'docs_display', '--pretty'])

    assert result.exit_code == 0
    assert json.loads(result.stdout) == {'content_type': 'text/html', 'body': '<html>docs</html>'}
