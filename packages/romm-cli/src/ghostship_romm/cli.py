from __future__ import annotations

import os
from typing import Any

import typer

from ghostship_cli_contract import DEFAULT_TIMEOUT, echo_json, parse_json_option, parse_params, require_env, run_app, run_cli_command

from .client import RommClient

HELP_TEXT = """RomM CLI interface.

Auth:
- Set ROMM_URL.
- Preferred: set ROMM_USERNAME and ROMM_PASSWORD.
- Optional override: set ROMM_TOKEN.
"""

app = typer.Typer(help=HELP_TEXT, no_args_is_help=True)
APP_STATE = {'timeout': DEFAULT_TIMEOUT}


@app.callback()
def app_callback(timeout: float = typer.Option(DEFAULT_TIMEOUT, '--timeout', help='Hard timeout in seconds for all API calls in this invocation.')) -> None:
    APP_STATE['timeout'] = timeout


def get_client() -> RommClient:
    return RommClient(require_env('ROMM_URL', os.getenv('ROMM_URL')), token=os.getenv('ROMM_TOKEN'), username=os.getenv('ROMM_USERNAME'), password=os.getenv('ROMM_PASSWORD'), default_timeout=APP_STATE['timeout'])


def _emit(data: Any, pretty: bool) -> None:
    echo_json(data, pretty=pretty)


def _run(execute, *, pretty: bool) -> None:
    _emit(run_cli_command(None, execute, timeout=APP_STATE['timeout']), pretty)


def _run_write(build_request, execute, *, dry_run: bool, pretty: bool) -> None:
    _emit(run_cli_command(build_request, execute, timeout=APP_STATE['timeout'], dry_run=dry_run), pretty)


@app.command('request')
def request(method: str, path: str, param: list[str] = typer.Option([], '--param'), body_json: str | None = typer.Option(None, '--body-json'), dry_run: bool = typer.Option(False, '--dry-run'), pretty: bool = typer.Option(False, '--pretty')) -> None:
    client = get_client()
    params = parse_params(param) or None
    payload = parse_json_option(body_json, '--body-json')
    _run_write(lambda: client.build_request(method, path, params=params, json_data=payload), lambda timeout: client.request(method, path, params=params, json_data=payload, timeout=timeout), dry_run=dry_run, pretty=pretty)


@app.command('get_heartbeat')
def get_heartbeat(pretty: bool = typer.Option(False, '--pretty')) -> None:
    client = get_client()
    _run(lambda timeout: client.get_heartbeat(timeout=timeout), pretty=pretty)


@app.command('get_platforms')
def get_platforms(pretty: bool = typer.Option(False, '--pretty')) -> None:
    client = get_client()
    _run(lambda timeout: client.get_platforms(timeout=timeout), pretty=pretty)


@app.command('get_libraries')
def get_libraries(pretty: bool = typer.Option(False, '--pretty')) -> None:
    client = get_client()
    _run(lambda timeout: client.get_libraries(timeout=timeout), pretty=pretty)


@app.command('get_roms')
def get_roms(page: int = typer.Option(1, '--page'), page_size: int = typer.Option(24, '--page-size'), platform: str | None = typer.Option(None, '--platform'), pretty: bool = typer.Option(False, '--pretty')) -> None:
    client = get_client()
    _run(lambda timeout: client.get_roms(page=page, page_size=page_size, platform=platform, timeout=timeout), pretty=pretty)


@app.command('get_rom')
def get_rom(rom_id: int, pretty: bool = typer.Option(False, '--pretty')) -> None:
    client = get_client()
    _run(lambda timeout: client.get_rom(rom_id, timeout=timeout), pretty=pretty)


@app.command('update_rom')
def update_rom(rom_id: int, body_json: str = typer.Option(..., '--body-json'), dry_run: bool = typer.Option(False, '--dry-run'), pretty: bool = typer.Option(False, '--pretty')) -> None:
    client = get_client()
    data = parse_json_option(body_json, '--body-json')
    _run_write(lambda: client.build_update_rom(rom_id, data), lambda timeout: client.update_rom(rom_id, data, timeout=timeout), dry_run=dry_run, pretty=pretty)


@app.command('delete_rom')
def delete_rom(rom_id: int, dry_run: bool = typer.Option(False, '--dry-run'), pretty: bool = typer.Option(False, '--pretty')) -> None:
    client = get_client()
    _run_write(lambda: client.build_delete_rom(rom_id), lambda timeout: client.delete_rom(rom_id, timeout=timeout), dry_run=dry_run, pretty=pretty)


@app.command('get_scans')
def get_scans(pretty: bool = typer.Option(False, '--pretty')) -> None:
    client = get_client()
    _run(lambda timeout: client.get_scans(timeout=timeout), pretty=pretty)


@app.command('start_scan')
def start_scan(library_id: int | None = typer.Option(None, '--library-id'), dry_run: bool = typer.Option(False, '--dry-run'), pretty: bool = typer.Option(False, '--pretty')) -> None:
    client = get_client()
    _run_write(lambda: client.build_start_scan(library_id), lambda timeout: client.start_scan(library_id, timeout=timeout), dry_run=dry_run, pretty=pretty)


@app.command('get_collections')
def get_collections(pretty: bool = typer.Option(False, '--pretty')) -> None:
    client = get_client()
    _run(lambda timeout: client.get_collections(timeout=timeout), pretty=pretty)


@app.command('get_config')
def get_config(pretty: bool = typer.Option(False, '--pretty')) -> None:
    client = get_client()
    _run(lambda timeout: client.get_config(timeout=timeout), pretty=pretty)


@app.command('get_saves')
def get_saves(page: int = typer.Option(1, '--page'), page_size: int = typer.Option(24, '--page-size'), pretty: bool = typer.Option(False, '--pretty')) -> None:
    client = get_client()
    _run(lambda timeout: client.get_saves(page=page, page_size=page_size, timeout=timeout), pretty=pretty)


@app.command('get_saves_summary')
def get_saves_summary(pretty: bool = typer.Option(False, '--pretty')) -> None:
    client = get_client()
    _run(lambda timeout: client.get_saves_summary(timeout=timeout), pretty=pretty)


@app.command('get_save')
def get_save(save_id: int, pretty: bool = typer.Option(False, '--pretty')) -> None:
    client = get_client()
    _run(lambda timeout: client.get_save(save_id, timeout=timeout), pretty=pretty)


@app.command('get_users')
def get_users(pretty: bool = typer.Option(False, '--pretty')) -> None:
    client = get_client()
    _run(lambda timeout: client.get_users(timeout=timeout), pretty=pretty)


@app.command('get_user_me')
def get_user_me(pretty: bool = typer.Option(False, '--pretty')) -> None:
    client = get_client()
    _run(lambda timeout: client.get_user_me(timeout=timeout), pretty=pretty)


def main() -> None:
    run_app(app)


if __name__ == '__main__':
    main()
