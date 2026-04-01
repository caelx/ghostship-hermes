from __future__ import annotations

import os
from typing import Any

import typer

from ghostship_cli_contract import DEFAULT_TIMEOUT, echo_json, parse_json_option, parse_params, require_env, run_app, run_cli_command

from .client import PyLoadClient

app = typer.Typer(help='pyLoad-ng CLI interface.', no_args_is_help=True)
APP_STATE = {'timeout': DEFAULT_TIMEOUT}


@app.callback()
def app_callback(timeout: float = typer.Option(DEFAULT_TIMEOUT, '--timeout', help='Hard timeout in seconds for all API calls in this invocation.')) -> None:
    APP_STATE['timeout'] = timeout


def get_client() -> PyLoadClient:
    return PyLoadClient(require_env('PYLOAD_URL', os.getenv('PYLOAD_URL')), os.getenv('PYLOAD_USER'), os.getenv('PYLOAD_PASS'), default_timeout=APP_STATE['timeout'])


def _emit(data: Any, pretty: bool) -> None:
    echo_json(data, pretty=pretty)


def _run(execute, *, pretty: bool) -> None:
    _emit(run_cli_command(None, execute, timeout=APP_STATE['timeout']), pretty)


def _run_write(build_request, execute, *, dry_run: bool, pretty: bool) -> None:
    _emit(run_cli_command(build_request, execute, timeout=APP_STATE['timeout'], dry_run=dry_run), pretty)


@app.command('request')
def request(method: str, path: str, param: list[str] = typer.Option([], '--param'), body_json: str | None = typer.Option(None, '--body-json'), dry_run: bool = typer.Option(False, '--dry-run'), pretty: bool = typer.Option(False, '--pretty')):
    client = get_client()
    params = parse_params(param) or None
    payload = parse_json_option(body_json, '--body-json')
    _run_write(lambda: client.build_request(method, path, params=params, json_data=payload), lambda timeout: client.request(method, path, params=params, json_data=payload, timeout=timeout), dry_run=dry_run, pretty=pretty)


@app.command('get_server_status')
def get_server_status(pretty: bool = typer.Option(False, '--pretty')):
    client = get_client()
    _run(lambda timeout: client.get_server_status(timeout=timeout), pretty=pretty)


@app.command('get_downloads')
def get_downloads(pretty: bool = typer.Option(False, '--pretty')):
    client = get_client()
    _run(lambda timeout: client.get_downloads(timeout=timeout), pretty=pretty)


@app.command('get_queue')
def get_queue(pretty: bool = typer.Option(False, '--pretty')):
    client = get_client()
    _run(lambda timeout: client.get_queue(timeout=timeout), pretty=pretty)


@app.command('add_package')
def add_package(name: str, links_json: str = typer.Option(..., '--links-json'), dry_run: bool = typer.Option(False, '--dry-run'), pretty: bool = typer.Option(False, '--pretty')):
    client = get_client()
    links = parse_json_option(links_json, '--links-json')
    _run_write(lambda: client.build_add_package(name, links), lambda timeout: client.add_package(name, links, timeout=timeout), dry_run=dry_run, pretty=pretty)


@app.command('add_files')
def add_files(package_id: int, links_json: str = typer.Option(..., '--links-json'), dry_run: bool = typer.Option(False, '--dry-run'), pretty: bool = typer.Option(False, '--pretty')):
    client = get_client()
    links = parse_json_option(links_json, '--links-json')
    _run_write(lambda: client.build_add_files(package_id, links), lambda timeout: client.add_files(package_id, links, timeout=timeout), dry_run=dry_run, pretty=pretty)


@app.command('delete_packages')
def delete_packages(package_ids_json: str = typer.Option(..., '--package-ids-json'), dry_run: bool = typer.Option(False, '--dry-run'), pretty: bool = typer.Option(False, '--pretty')):
    client = get_client()
    package_ids = parse_json_option(package_ids_json, '--package-ids-json')
    _run_write(lambda: client.build_delete_packages(package_ids), lambda timeout: client.delete_packages(package_ids, timeout=timeout), dry_run=dry_run, pretty=pretty)


@app.command('toggle_pause')
def toggle_pause(dry_run: bool = typer.Option(False, '--dry-run'), pretty: bool = typer.Option(False, '--pretty')):
    client = get_client()
    _run_write(lambda: client.build_toggle_pause(), lambda timeout: client.toggle_pause(timeout=timeout), dry_run=dry_run, pretty=pretty)


@app.command('get_config')
def get_config(pretty: bool = typer.Option(False, '--pretty')):
    client = get_client()
    _run(lambda timeout: client.get_config(timeout=timeout), pretty=pretty)


@app.command('delete_finished')
def delete_finished(dry_run: bool = typer.Option(False, '--dry-run'), pretty: bool = typer.Option(False, '--pretty')):
    client = get_client()
    _run_write(lambda: client.build_delete_finished(), lambda timeout: client.delete_finished(timeout=timeout), dry_run=dry_run, pretty=pretty)


@app.command('restart_failed')
def restart_failed(dry_run: bool = typer.Option(False, '--dry-run'), pretty: bool = typer.Option(False, '--pretty')):
    client = get_client()
    _run_write(lambda: client.build_restart_failed(), lambda timeout: client.restart_failed(timeout=timeout), dry_run=dry_run, pretty=pretty)


@app.command('stop_all_downloads')
def stop_all_downloads(dry_run: bool = typer.Option(False, '--dry-run'), pretty: bool = typer.Option(False, '--pretty')):
    client = get_client()
    _run_write(lambda: client.build_stop_all_downloads(), lambda timeout: client.stop_all_downloads(timeout=timeout), dry_run=dry_run, pretty=pretty)


@app.command('get_accounts')
def get_accounts(refresh: bool = typer.Option(False, '--refresh'), pretty: bool = typer.Option(False, '--pretty')):
    client = get_client()
    _run(lambda timeout: client.get_accounts(refresh=refresh, timeout=timeout), pretty=pretty)


@app.command('add_account')
def add_account(plugin: str, login: str, password: str, dry_run: bool = typer.Option(False, '--dry-run'), pretty: bool = typer.Option(False, '--pretty')):
    client = get_client()
    _run_write(lambda: client.build_add_account(plugin, login, password), lambda timeout: client.add_account(plugin, login, password, timeout=timeout), dry_run=dry_run, pretty=pretty)


@app.command('remove_account')
def remove_account(plugin: str, login: str, dry_run: bool = typer.Option(False, '--dry-run'), pretty: bool = typer.Option(False, '--pretty')):
    client = get_client()
    _run_write(lambda: client.build_remove_account(plugin, login), lambda timeout: client.remove_account(plugin, login, timeout=timeout), dry_run=dry_run, pretty=pretty)


@app.command('get_server_version')
def get_server_version(pretty: bool = typer.Option(False, '--pretty')):
    client = get_client()
    _run(lambda timeout: client.get_server_version(timeout=timeout), pretty=pretty)


@app.command('get_free_space')
def get_free_space(pretty: bool = typer.Option(False, '--pretty')):
    client = get_client()
    _run(lambda timeout: client.get_free_space(timeout=timeout), pretty=pretty)


def main():
    run_app(app)


if __name__ == '__main__':
    main()
