from __future__ import annotations

import os
from typing import Any

import typer

from ghostship_cli_contract import (
    ConfigError,
    DEFAULT_TIMEOUT,
    echo_json,
    handle_cli_error,
    parse_file_params,
    parse_json_option,
    parse_params,
    require_env,
    run_app,
    run_cli_command,
    write_response_output,
)

from .catalog import MUTATING_METHODS, OPERATIONS, OperationDef
from .client import BookStackClient

app = typer.Typer(help='Typed BookStack REST API CLI.', no_args_is_help=True)
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


def get_client() -> BookStackClient:
    base_url = require_env('BOOKSTACK_URL', os.getenv('BOOKSTACK_URL'))
    token_id = require_env('BOOKSTACK_TOKEN_ID', os.getenv('BOOKSTACK_TOKEN_ID'))
    token_secret = require_env('BOOKSTACK_TOKEN_SECRET', os.getenv('BOOKSTACK_TOKEN_SECRET'))
    return BookStackClient(base_url, token_id, token_secret, default_timeout=APP_STATE['timeout'])


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
    form_param: list[str] = typer.Option([], '--form-param', help='Repeat key=value form parameters.'),
    file: list[str] = typer.Option([], '--file', help='Repeat key=path file uploads.'),
    body_json: str | None = typer.Option(None, '--body-json', help='Optional JSON request body.'),
    output: str | None = typer.Option(None, '--output', help='Optional output file path for non-JSON/binary responses.'),
    dry_run: bool = typer.Option(False, '--dry-run', help='Print the request JSON and do not call the API.'),
    pretty: bool = typer.Option(False, '--pretty', help='Pretty print JSON output.'),
) -> None:
    payload = parse_json_option(body_json, '--body-json')
    params = _parse_named_params(query_param)
    form_data = _parse_named_params(form_param)
    files = parse_file_params(file) or None
    if payload is not None and (form_data is not None or files is not None):
        raise ConfigError('use either --body-json or form/file parameters, not both')
    normalized_path = path if path.startswith('/') else f'/{path}'
    client = get_client()
    _run_write(
        lambda: client.build_request(method, normalized_path, query_params=params, json_body=payload, form_data=form_data, files=files, timeout=APP_STATE['timeout']),
        lambda timeout: write_response_output(client.request_response(method, normalized_path, query_params=params, json_body=payload, form_data=form_data, files=files, timeout=timeout), output) if output else client.request(method, normalized_path, query_params=params, json_body=payload, form_data=form_data, files=files, timeout=timeout),
        dry_run=dry_run,
        pretty=pretty,
    )


def _operation_help(operation: OperationDef) -> str:
    path_bits = ', '.join(operation.path_params) if operation.path_params else 'none'
    query_bits = ', '.join(operation.query_params) if operation.query_params else 'any supported upstream query parameter'
    body_bits = ', '.join(operation.body_params) if operation.body_params else 'none'
    response_bit = f'response kind: {operation.response_kind}'
    form_bit = 'multipart capable' if operation.multipart else 'json/body only'
    return f"{operation.summary} Path params: {path_bits}. Query params: {query_bits}. Body params: {body_bits}. {form_bit}. {response_bit}."


def _register_operation(operation: OperationDef) -> None:
    supports_dry_run = operation.method in MUTATING_METHODS

    def _command(
        path_param: list[str] = typer.Option([], '--path-param', help='Repeat name=value path parameters.'),
        query_param: list[str] = typer.Option([], '--query-param', help='Repeat key=value query parameters.'),
        form_param: list[str] = typer.Option([], '--form-param', help='Repeat key=value form parameters.'),
        file: list[str] = typer.Option([], '--file', help='Repeat key=path file uploads.'),
        body_json: str | None = typer.Option(None, '--body-json', help='Optional JSON request body.'),
        output: str | None = typer.Option(None, '--output', help='Required output file path for binary response operations.'),
        dry_run: bool = typer.Option(False, '--dry-run', help='Print the request JSON and do not call the API.'),
        pretty: bool = typer.Option(False, '--pretty', help='Pretty print JSON output.'),
    ) -> None:
        if dry_run and not supports_dry_run:
            raise ConfigError('--dry-run is only supported for write and delete commands')
        payload = parse_json_option(body_json, '--body-json')
        path_params = _parse_named_params(path_param)
        query_params = _parse_named_params(query_param)
        form_data = _parse_named_params(form_param)
        files = parse_file_params(file) or None
        if payload is not None and (form_data is not None or files is not None):
            raise ConfigError('use either --body-json or form/file parameters, not both')
        if operation.response_kind == 'binary' and not dry_run and output is None:
            raise ConfigError('--output is required for binary response operations')
        client = get_client()
        _run_write(
            lambda: client.build_operation_request(
                operation.command_name,
                path_params=path_params,
                query_params=query_params,
                json_body=payload,
                form_data=form_data,
                files=files,
                timeout=APP_STATE['timeout'],
            ),
            lambda timeout: write_response_output(
                client.request_operation(
                    operation.command_name,
                    path_params=path_params,
                    query_params=query_params,
                    json_body=payload,
                    form_data=form_data,
                    files=files,
                    timeout=timeout,
                ),
                output,
            ) if operation.response_kind == 'binary' else client.request_operation(
                operation.command_name,
                path_params=path_params,
                query_params=query_params,
                json_body=payload,
                form_data=form_data,
                files=files,
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
