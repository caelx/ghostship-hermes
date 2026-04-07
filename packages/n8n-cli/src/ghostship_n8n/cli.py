from __future__ import annotations

import os
from typing import Any

import typer

from ghostship_cli_contract import (
    ConfigError,
    DEFAULT_TIMEOUT,
    echo_json,
    handle_cli_error,
    parse_json_option,
    parse_params,
    require_env,
    run_app,
    run_cli_command,
)

from .catalog import MUTATING_METHODS, OPERATIONS, OperationDef
from .client import N8nClient

app = typer.Typer(help='Typed n8n Public API CLI.', no_args_is_help=True)
APP_STATE = {'timeout': DEFAULT_TIMEOUT}


@app.callback()
def app_callback(
    timeout: float = typer.Option(
        DEFAULT_TIMEOUT,
        '--timeout',
        help='Hard timeout in seconds for all API calls in this invocation.',
    )
) -> None:
    APP_STATE['timeout'] = timeout


def get_client() -> N8nClient:
    base_url = require_env('N8N_URL', os.getenv('N8N_URL'))
    api_key = require_env('N8N_API_KEY', os.getenv('N8N_API_KEY'))
    api_path = os.getenv('N8N_PUBLIC_API_ENDPOINT', 'api')
    api_version = os.getenv('N8N_PUBLIC_API_VERSION', 'v1')
    return N8nClient(
        base_url,
        api_key,
        api_path=api_path,
        api_version=api_version,
        default_timeout=APP_STATE['timeout'],
    )


def _emit(data: Any, *, pretty: bool) -> None:
    echo_json(data, pretty=pretty)


def _run_write(build_request, execute, *, dry_run: bool, pretty: bool) -> None:
    try:
        result = run_cli_command(
            build_request,
            execute,
            timeout=APP_STATE['timeout'],
            dry_run=dry_run,
        )
        _emit(result, pretty=pretty)
    except Exception as exc:  # pragma: no cover
        handle_cli_error(exc)


def _parse_named_params(values: list[str]) -> dict[str, str] | None:
    params = parse_params(values)
    return params or None


@app.command('request')
def request(
    method: str,
    path: str,
    query_param: list[str] = typer.Option([], '--query-param', help='Repeat key=value query parameters.'),
    body_json: str | None = typer.Option(None, '--body-json', help='Optional JSON request body.'),
    dry_run: bool = typer.Option(False, '--dry-run', help='Print the request JSON and do not call the API.'),
    pretty: bool = typer.Option(False, '--pretty', help='Pretty print JSON output.'),
) -> None:
    payload = parse_json_option(body_json, '--body-json')
    params = _parse_named_params(query_param)
    normalized_path = path if path.startswith('/') else f'/{path}'
    client = get_client()
    _run_write(
        lambda: client.build_request(method, normalized_path, query_params=params, json_body=payload, timeout=APP_STATE['timeout']),
        lambda timeout: client.request_json(method, normalized_path, params=params, json_body=payload, timeout=timeout),
        dry_run=dry_run,
        pretty=pretty,
    )


def _operation_help(operation: OperationDef) -> str:
    path_bits = ', '.join(operation.path_params) if operation.path_params else 'none'
    query_bits = ', '.join(operation.query_params) if operation.query_params else 'any supported upstream query parameter'
    body_bit = 'accepts JSON request body' if operation.has_body else 'no JSON request body'
    return f"{operation.summary} Path params: {path_bits}. Query params: {query_bits}. {body_bit}."


def _register_operation(operation: OperationDef) -> None:
    supports_dry_run = operation.method in MUTATING_METHODS

    def _command(
        path_param: list[str] = typer.Option([], '--path-param', help='Repeat name=value path parameters.'),
        query_param: list[str] = typer.Option([], '--query-param', help='Repeat key=value query parameters.'),
        body_json: str | None = typer.Option(None, '--body-json', help='Optional JSON request body.'),
        dry_run: bool = typer.Option(False, '--dry-run', help='Print the request JSON and do not call the API.'),
        pretty: bool = typer.Option(False, '--pretty', help='Pretty print JSON output.'),
    ) -> None:
        if dry_run and not supports_dry_run:
            raise ConfigError('--dry-run is only supported for write and delete commands')
        payload = parse_json_option(body_json, '--body-json')
        path_params = _parse_named_params(path_param)
        query_params = _parse_named_params(query_param)
        client = get_client()
        _run_write(
            lambda: client.build_operation_request(
                operation.command_name,
                path_params=path_params,
                query_params=query_params,
                json_body=payload,
                timeout=APP_STATE['timeout'],
            ),
            lambda timeout: client.request_operation(
                operation.command_name,
                path_params=path_params,
                query_params=query_params,
                json_body=payload,
                timeout=timeout,
            ),
            dry_run=dry_run,
            pretty=pretty,
        )

    _command.__name__ = f'cmd_{operation.command_name}'
    app.command(operation.command_name, help=_operation_help(operation))(_command)


for _operation in OPERATIONS:
    _register_operation(_operation)


def main() -> None:
    run_app(app)


if __name__ == '__main__':
    main()
