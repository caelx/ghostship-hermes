from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Callable

import typer

from ghostship_cli_contract import (
    DEFAULT_TIMEOUT,
    echo_json,
    handle_cli_error,
    parse_json_option,
    require_env,
    run_app,
    run_cli_command,
)

from .client import SynologyClient

app = typer.Typer(help='Synology File Station CLI interface.', no_args_is_help=True)
APP_STATE = {'timeout': DEFAULT_TIMEOUT}


@app.callback()
def app_callback(timeout: float = typer.Option(DEFAULT_TIMEOUT, '--timeout', help='Hard timeout in seconds for all API calls in this invocation.')) -> None:
    APP_STATE['timeout'] = timeout


def get_client() -> SynologyClient:
    base_url = require_env('SYNOLOGY_URL', os.getenv('SYNOLOGY_URL'))
    username = require_env('SYNOLOGY_USER', os.getenv('SYNOLOGY_USER'))
    password = require_env('SYNOLOGY_PASS', os.getenv('SYNOLOGY_PASS'))
    verify_ssl = os.getenv('SYNOLOGY_VERIFY_SSL', 'true').lower() == 'true'
    return SynologyClient(base_url, username, password, verify_ssl, default_timeout=APP_STATE['timeout'])


def _emit(result: Any, *, pretty: bool) -> None:
    echo_json(result, pretty=pretty)


def _run_with_session(execute: Callable[[SynologyClient, float], Any], *, pretty: bool) -> None:
    try:
        client = get_client()
        client.login(timeout=APP_STATE['timeout'])
        try:
            result = execute(client, APP_STATE['timeout'])
        finally:
            client.logout(timeout=APP_STATE['timeout'])
        _emit(result, pretty=pretty)
    except Exception as exc:  # pragma: no cover
        handle_cli_error(exc)


def _run_write(build_request: Callable[[SynologyClient], Any], execute: Callable[[SynologyClient, float], Any], *, dry_run: bool, pretty: bool) -> None:
    try:
        client = get_client()
        result = run_cli_command(lambda: build_request(client), lambda timeout: _execute_logged_in(client, execute, timeout), timeout=APP_STATE['timeout'], dry_run=dry_run)
        _emit(result, pretty=pretty)
    except Exception as exc:  # pragma: no cover
        handle_cli_error(exc)


def _execute_logged_in(client: SynologyClient, execute: Callable[[SynologyClient, float], Any], timeout: float) -> Any:
    client.login(timeout=timeout)
    try:
        return execute(client, timeout)
    finally:
        client.logout(timeout=timeout)


@app.command('call')
def call(
    api: str,
    method_name: str,
    version: int | None = typer.Option(None, '--version'),
    path: str | None = typer.Option(None, '--path'),
    param_json: str | None = typer.Option(None, '--param-json'),
    http_method: str | None = typer.Option(None, '--http-method'),
    dry_run: bool = typer.Option(False, '--dry-run', help='Print the request JSON and do not call the API.'),
    pretty: bool = typer.Option(False, '--pretty', help='Pretty print JSON output'),
) -> None:
    params = parse_json_option(param_json, '--param-json')
    _run_write(
        lambda client: client.build_call(api, method_name, version=version, path=path, params=params, http_method=http_method, timeout=APP_STATE['timeout']),
        lambda client, timeout: client.call(api, method_name, version=version, path=path, params=params, http_method=http_method, timeout=timeout),
        dry_run=dry_run,
        pretty=pretty,
    )


@app.command('get_info')
def get_info(query: str = typer.Option('all', '--query'), pretty: bool = typer.Option(False, '--pretty', help='Pretty print JSON output')) -> None:
    _run_with_session(lambda client, timeout: client.get_info(query=query, timeout=timeout), pretty=pretty)


@app.command('login')
def login(dry_run: bool = typer.Option(False, '--dry-run', help='Print the request JSON and do not call the API.'), pretty: bool = typer.Option(False, '--pretty', help='Pretty print JSON output')) -> None:
    try:
        client = get_client()
        result = run_cli_command(lambda: client.build_login(timeout=APP_STATE['timeout']), lambda timeout: {'sid': _login_for_output(client, timeout)}, timeout=APP_STATE['timeout'], dry_run=dry_run)
        if not dry_run and client.sid:
            client.logout(timeout=APP_STATE['timeout'])
        _emit(result, pretty=pretty)
    except Exception as exc:  # pragma: no cover
        handle_cli_error(exc)


def _login_for_output(client: SynologyClient, timeout: float) -> str:
    return client.login(timeout=timeout)


@app.command('logout')
def logout(dry_run: bool = typer.Option(False, '--dry-run', help='Print the request JSON and do not call the API.'), pretty: bool = typer.Option(False, '--pretty', help='Pretty print JSON output')) -> None:
    _run_write(lambda client: client.build_logout(timeout=APP_STATE['timeout']), lambda client, timeout: {'ok': _logout_after_login(client, timeout)}, dry_run=dry_run, pretty=pretty)


def _logout_after_login(client: SynologyClient, timeout: float) -> bool:
    client.login(timeout=timeout)
    return client.logout(timeout=timeout)


@app.command('list_shares')
def list_shares(pretty: bool = typer.Option(False, '--pretty', help='Pretty print JSON output')) -> None:
    _run_with_session(lambda client, timeout: client.list_shares(timeout=timeout), pretty=pretty)


@app.command('list_files')
def list_files(folder_path: str, offset: int = typer.Option(0, '--offset'), limit: int = typer.Option(100, '--limit'), sort_by: str = typer.Option('name', '--sort-by'), pretty: bool = typer.Option(False, '--pretty', help='Pretty print JSON output')) -> None:
    _run_with_session(lambda client, timeout: client.list_files(folder_path, offset=offset, limit=limit, sort_by=sort_by, timeout=timeout), pretty=pretty)


@app.command('get_file_info')
def get_file_info(path: str, pretty: bool = typer.Option(False, '--pretty', help='Pretty print JSON output')) -> None:
    _run_with_session(lambda client, timeout: client.get_file_info(path, timeout=timeout), pretty=pretty)


@app.command('search_start')
def search_start(folder_path: str, pattern: str, recursive: bool = typer.Option(True, '--recursive/--no-recursive'), dry_run: bool = typer.Option(False, '--dry-run', help='Print the request JSON and do not call the API.'), pretty: bool = typer.Option(False, '--pretty', help='Pretty print JSON output')) -> None:
    _run_write(lambda client: client.build_search_start(folder_path, pattern, recursive=recursive, timeout=APP_STATE['timeout']), lambda client, timeout: {'taskid': client.search_start(folder_path, pattern, recursive=recursive, timeout=timeout)}, dry_run=dry_run, pretty=pretty)


@app.command('search_list')
def search_list(taskid: str, offset: int = typer.Option(0, '--offset'), limit: int = typer.Option(100, '--limit'), pretty: bool = typer.Option(False, '--pretty', help='Pretty print JSON output')) -> None:
    _run_with_session(lambda client, timeout: client.search_list(taskid, offset=offset, limit=limit, timeout=timeout), pretty=pretty)


@app.command('create_folder')
def create_folder(folder_path: str, name: str, force_parent: bool = typer.Option(False, '--force-parent'), dry_run: bool = typer.Option(False, '--dry-run', help='Print the request JSON and do not call the API.'), pretty: bool = typer.Option(False, '--pretty', help='Pretty print JSON output')) -> None:
    _run_write(lambda client: client.build_create_folder(folder_path, name, force_parent=force_parent, timeout=APP_STATE['timeout']), lambda client, timeout: client.create_folder(folder_path, name, force_parent=force_parent, timeout=timeout), dry_run=dry_run, pretty=pretty)


@app.command('rename')
def rename(path: str, name: str, dry_run: bool = typer.Option(False, '--dry-run', help='Print the request JSON and do not call the API.'), pretty: bool = typer.Option(False, '--pretty', help='Pretty print JSON output')) -> None:
    _run_write(lambda client: client.build_rename(path, name, timeout=APP_STATE['timeout']), lambda client, timeout: client.rename(path, name, timeout=timeout), dry_run=dry_run, pretty=pretty)


@app.command('delete')
def delete(path: str, recursive: bool = typer.Option(True, '--recursive/--no-recursive'), dry_run: bool = typer.Option(False, '--dry-run', help='Print the request JSON and do not call the API.'), pretty: bool = typer.Option(False, '--pretty', help='Pretty print JSON output')) -> None:
    _run_write(lambda client: client.build_delete(path, recursive=recursive, timeout=APP_STATE['timeout']), lambda client, timeout: {'taskid': client.delete(path, recursive=recursive, timeout=timeout)}, dry_run=dry_run, pretty=pretty)


@app.command('download_file')
def download_file(path: str, mode: str = typer.Option('download', '--mode'), output: str = typer.Option('.', '--output'), pretty: bool = typer.Option(False, '--pretty', help='Pretty print JSON output')) -> None:
    def _download(client: SynologyClient, timeout: float):
        response = client.download_file(path, mode=mode, timeout=timeout)
        output_path = Path(output)
        destination = output_path / Path(path).name if output_path.is_dir() else output_path
        destination.write_bytes(response.content)
        return {'path': path, 'output': str(destination)}

    _run_with_session(_download, pretty=pretty)


@app.command('upload_file')
def upload_file(folder_path: str, file_path: str, create_parents: bool = typer.Option(True, '--create-parents/--no-create-parents'), dry_run: bool = typer.Option(False, '--dry-run', help='Print the request JSON and do not call the API.'), pretty: bool = typer.Option(False, '--pretty', help='Pretty print JSON output')) -> None:
    _run_write(lambda client: client.build_upload_file(folder_path, file_path, create_parents=create_parents, timeout=APP_STATE['timeout']), lambda client, timeout: client.upload_file(folder_path, file_path, create_parents=create_parents, timeout=timeout), dry_run=dry_run, pretty=pretty)


@app.command('copy')
def copy(path: str, destination: str, overwrite: bool = typer.Option(True, '--overwrite/--no-overwrite'), dry_run: bool = typer.Option(False, '--dry-run', help='Print the request JSON and do not call the API.'), pretty: bool = typer.Option(False, '--pretty', help='Pretty print JSON output')) -> None:
    _run_write(lambda client: client.build_copy(path, destination, overwrite=overwrite, timeout=APP_STATE['timeout']), lambda client, timeout: client.copy(path, destination, overwrite=overwrite, timeout=timeout), dry_run=dry_run, pretty=pretty)


@app.command('move')
def move(path: str, destination: str, overwrite: bool = typer.Option(True, '--overwrite/--no-overwrite'), dry_run: bool = typer.Option(False, '--dry-run', help='Print the request JSON and do not call the API.'), pretty: bool = typer.Option(False, '--pretty', help='Pretty print JSON output')) -> None:
    _run_write(lambda client: client.build_move(path, destination, overwrite=overwrite, timeout=APP_STATE['timeout']), lambda client, timeout: client.move(path, destination, overwrite=overwrite, timeout=timeout), dry_run=dry_run, pretty=pretty)


def main() -> None:
    run_app(app)


if __name__ == '__main__':
    main()
