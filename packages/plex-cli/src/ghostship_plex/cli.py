from __future__ import annotations

import os
from typing import Any

import typer

from ghostship_cli_contract import DEFAULT_TIMEOUT, echo_json, parse_json_option, parse_params, require_env, run_app, run_cli_command

from .client import PlexClient

app = typer.Typer(help='Plex Media Server CLI interface.', no_args_is_help=True)
APP_STATE = {'timeout': DEFAULT_TIMEOUT}


@app.callback()
def app_callback(timeout: float = typer.Option(DEFAULT_TIMEOUT, '--timeout', help='Hard timeout in seconds for all API calls in this invocation.')) -> None:
    APP_STATE['timeout'] = timeout


def get_client() -> PlexClient:
    return PlexClient(require_env('PLEX_URL', os.getenv('PLEX_URL')), require_env('PLEX_TOKEN', os.getenv('PLEX_TOKEN')), default_timeout=APP_STATE['timeout'])


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


@app.command('get_identity')
def get_identity(pretty: bool = typer.Option(False, '--pretty')) -> None:
    client = get_client()
    _run(lambda timeout: client.get_identity(timeout=timeout), pretty=pretty)


@app.command('get_server_info')
def get_server_info(pretty: bool = typer.Option(False, '--pretty')) -> None:
    client = get_client()
    _run(lambda timeout: client.get_server_info(timeout=timeout), pretty=pretty)


@app.command('get_status_sessions')
def get_status_sessions(pretty: bool = typer.Option(False, '--pretty')) -> None:
    client = get_client()
    _run(lambda timeout: client.get_status_sessions(timeout=timeout), pretty=pretty)


@app.command('get_activities')
def get_activities(pretty: bool = typer.Option(False, '--pretty')) -> None:
    client = get_client()
    _run(lambda timeout: client.get_activities(timeout=timeout), pretty=pretty)


@app.command('get_library_sections')
def get_library_sections(pretty: bool = typer.Option(False, '--pretty')) -> None:
    client = get_client()
    _run(lambda timeout: client.get_library_sections(timeout=timeout), pretty=pretty)


@app.command('get_library_section')
def get_library_section(section_id: int, pretty: bool = typer.Option(False, '--pretty')) -> None:
    client = get_client()
    _run(lambda timeout: client.get_library_section(section_id, timeout=timeout), pretty=pretty)


@app.command('get_library_filters')
def get_library_filters(section_id: int, pretty: bool = typer.Option(False, '--pretty')) -> None:
    client = get_client()
    _run(lambda timeout: client.get_library_filters(section_id, timeout=timeout), pretty=pretty)


@app.command('get_library_sorts')
def get_library_sorts(section_id: int, pretty: bool = typer.Option(False, '--pretty')) -> None:
    client = get_client()
    _run(lambda timeout: client.get_library_sorts(section_id, timeout=timeout), pretty=pretty)


@app.command('refresh_library')
def refresh_library(section_id: int | None = typer.Option(None, '--section-id'), dry_run: bool = typer.Option(False, '--dry-run'), pretty: bool = typer.Option(False, '--pretty')) -> None:
    client = get_client()
    _run_write(lambda: client.build_refresh_library(section_id), lambda timeout: client.refresh_library(section_id, timeout=timeout), dry_run=dry_run, pretty=pretty)


@app.command('get_metadata')
def get_metadata(rating_key: int, pretty: bool = typer.Option(False, '--pretty')) -> None:
    client = get_client()
    _run(lambda timeout: client.get_metadata(rating_key, timeout=timeout), pretty=pretty)


@app.command('get_metadata_children')
def get_metadata_children(rating_key: int, pretty: bool = typer.Option(False, '--pretty')) -> None:
    client = get_client()
    _run(lambda timeout: client.get_metadata_children(rating_key, timeout=timeout), pretty=pretty)


@app.command('get_playlists')
def get_playlists(pretty: bool = typer.Option(False, '--pretty')) -> None:
    client = get_client()
    _run(lambda timeout: client.get_playlists(timeout=timeout), pretty=pretty)


@app.command('get_playlist_items')
def get_playlist_items(playlist_id: int, pretty: bool = typer.Option(False, '--pretty')) -> None:
    client = get_client()
    _run(lambda timeout: client.get_playlist_items(playlist_id, timeout=timeout), pretty=pretty)


@app.command('get_collections')
def get_collections(section_id: int, pretty: bool = typer.Option(False, '--pretty')) -> None:
    client = get_client()
    _run(lambda timeout: client.get_collections(section_id, timeout=timeout), pretty=pretty)


@app.command('get_preferences')
def get_preferences(pretty: bool = typer.Option(False, '--pretty')) -> None:
    client = get_client()
    _run(lambda timeout: client.get_preferences(timeout=timeout), pretty=pretty)


@app.command('get_butler_tasks')
def get_butler_tasks(pretty: bool = typer.Option(False, '--pretty')) -> None:
    client = get_client()
    _run(lambda timeout: client.get_butler_tasks(timeout=timeout), pretty=pretty)


@app.command('get_statistics')
def get_statistics(pretty: bool = typer.Option(False, '--pretty')) -> None:
    client = get_client()
    _run(lambda timeout: client.get_statistics(timeout=timeout), pretty=pretty)


@app.command('terminate_session')
def terminate_session(session_id: int, dry_run: bool = typer.Option(False, '--dry-run'), pretty: bool = typer.Option(False, '--pretty')) -> None:
    client = get_client()
    _run_write(lambda: client.build_terminate_session(session_id), lambda timeout: client.terminate_session(session_id, timeout=timeout), dry_run=dry_run, pretty=pretty)


@app.command('get_session')
def get_session(session_id: int, pretty: bool = typer.Option(False, '--pretty')) -> None:
    client = get_client()
    _run(lambda timeout: client.get_session(session_id, timeout=timeout), pretty=pretty)


def main() -> None:
    run_app(app)


if __name__ == '__main__':
    main()
