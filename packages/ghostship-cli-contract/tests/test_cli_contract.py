from __future__ import annotations

import json

import httpx
import pytest

from ghostship_cli_contract.cli import render_dry_run, run_cli_command
from ghostship_cli_contract.errors import (
    CliContractError,
    ConfigError,
    HttpStatusError,
    InvalidInputError,
    ResponseDecodeError,
    TimeoutError,
    TransportError,
    UnknownCliError,
    exit_code_for_error,
)
from ghostship_cli_contract.http import BaseHttpClient
from ghostship_cli_contract.models import RequestSpec


def test_request_spec_to_dict_omits_empty_fields() -> None:
    spec = RequestSpec(method='POST', path='/api/test', timeout=30.0, json_body={'name': 'demo'})

    assert spec.to_dict() == {
        'method': 'POST',
        'path': '/api/test',
        'timeout': 30.0,
        'json_body': {'name': 'demo'},
    }


def test_request_spec_to_dict_includes_raw_content() -> None:
    spec = RequestSpec(method='POST', path='/api/import', timeout=30.0, content='https://example.com')

    assert spec.to_dict() == {
        'method': 'POST',
        'path': '/api/import',
        'timeout': 30.0,
        'content': 'https://example.com',
    }


def test_render_dry_run_returns_jsonable_request() -> None:
    spec = RequestSpec(method='DELETE', path='/api/items/7', timeout=12.5, params={'force': 'true'})

    assert render_dry_run(spec) == {
        'method': 'DELETE',
        'path': '/api/items/7',
        'timeout': 12.5,
        'params': {'force': 'true'},
    }


@pytest.mark.parametrize(
    ('error', 'code'),
    [
        (InvalidInputError('bad input'), 2),
        (ConfigError('missing env'), 3),
        (TimeoutError('timeout'), 4),
        (HttpStatusError('boom', status_code=502), 5),
        (TransportError('connect failed'), 6),
        (ResponseDecodeError('bad json'), 7),
        (UnknownCliError('oops'), 10),
    ],
)
def test_exit_code_mapping(error: CliContractError, code: int) -> None:
    assert exit_code_for_error(error) == code


def test_run_cli_command_returns_dry_run_payload() -> None:
    spec = RequestSpec(method='POST', path='/api/items', timeout=30.0, json_body={'a': 1})

    result = run_cli_command(lambda: spec, lambda timeout: {'ok': True}, timeout=30.0, dry_run=True)

    assert result == spec.to_dict()


def test_run_cli_command_executes_callable_when_not_dry_run() -> None:
    result = run_cli_command(lambda: RequestSpec(method='GET', path='/health', timeout=5.0), lambda timeout: {'timeout': timeout}, timeout=5.0)

    assert result == {'timeout': 5.0}


def test_base_http_client_uses_default_timeout() -> None:
    transport = httpx.MockTransport(lambda request: httpx.Response(200, json={'ok': True}))
    client = BaseHttpClient('https://example.test', default_headers={'X-Test': '1'}, transport=transport)

    assert client.request_json('GET', '/health') == {'ok': True}


def test_base_http_client_allows_timeout_override() -> None:
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen['url'] = str(request.url)
        return httpx.Response(200, json={'ok': True})

    transport = httpx.MockTransport(handler)
    client = BaseHttpClient('https://example.test', transport=transport)

    assert client.request_json('GET', '/health', timeout=4.5) == {'ok': True}
    assert seen['url'] == 'https://example.test/health'


def test_base_http_client_supports_raw_content_body() -> None:
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen['content_type'] = request.headers.get('Content-Type')
        seen['body'] = request.content.decode()
        return httpx.Response(200, json={'ok': True})

    transport = httpx.MockTransport(handler)
    client = BaseHttpClient('https://example.test', transport=transport)

    assert client.request_json('POST', '/import', content='https://example.com', headers={'Content-Type': 'text/plain'}) == {'ok': True}
    assert seen == {'content_type': 'text/plain', 'body': 'https://example.com'}


def test_base_http_client_raises_timeout_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout('timed out', request=request)

    client = BaseHttpClient('https://example.test', transport=httpx.MockTransport(handler))

    with pytest.raises(TimeoutError):
        client.request_json('GET', '/health')


def test_base_http_client_raises_http_status_error() -> None:
    transport = httpx.MockTransport(lambda request: httpx.Response(404, json={'message': 'missing'}, request=request))
    client = BaseHttpClient('https://example.test', transport=transport)

    with pytest.raises(HttpStatusError) as exc:
        client.request_json('GET', '/missing')

    assert exc.value.status_code == 404


def test_base_http_client_raises_decode_error() -> None:
    transport = httpx.MockTransport(lambda request: httpx.Response(200, content=b'not-json'))
    client = BaseHttpClient('https://example.test', transport=transport)

    with pytest.raises(ResponseDecodeError):
        client.request_json('GET', '/broken')


def test_run_app_maps_click_usage_errors_to_json_exit() -> None:
    import click
    import typer

    app = typer.Typer()

    @app.command()
    def broken() -> None:
        raise click.BadParameter('bad value', param_hint='--name')

    with pytest.raises(typer.Exit) as exc:
        from ghostship_cli_contract.cli import run_app
        run_app(app, ['broken'])

    assert exc.value.exit_code == 2


def test_handle_cli_error_writes_json_to_stderr(capsys: pytest.CaptureFixture[str]) -> None:
    import typer

    from ghostship_cli_contract.cli import handle_cli_error

    with pytest.raises(typer.Exit) as exc:
        handle_cli_error(ConfigError('missing env'))

    assert exc.value.exit_code == 3
    captured = capsys.readouterr()
    payload = json.loads(captured.err)
    assert payload['error']['type'] == 'ConfigError'


def test_base_http_client_request_json_bypasses_service_request_override() -> None:
    class DerivedClient(BaseHttpClient):
        def request(self, method, path, **kwargs):  # type: ignore[override]
            raise AssertionError('service-level request override should not be used by request_json')

    transport = httpx.MockTransport(lambda request: httpx.Response(200, json={'ok': True}))
    client = DerivedClient('https://example.test', transport=transport)

    assert client.request_json('GET', '/health') == {'ok': True}
