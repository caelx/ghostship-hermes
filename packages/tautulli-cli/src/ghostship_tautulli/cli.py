from __future__ import annotations

import os
from typing import Any

import typer

from ghostship_cli_contract import DEFAULT_TIMEOUT, echo_json, parse_json_option, require_env, run_app, run_cli_command

from .client import TautulliClient

app = typer.Typer(help='Tautulli CLI interface.', no_args_is_help=True)
APP_STATE = {'timeout': DEFAULT_TIMEOUT}


@app.callback()
def app_callback(timeout: float = typer.Option(DEFAULT_TIMEOUT, '--timeout', help='Hard timeout in seconds for all API calls in this invocation.')) -> None:
    APP_STATE['timeout'] = timeout


def get_client() -> TautulliClient:
    return TautulliClient(require_env('TAUTULLI_URL', os.getenv('TAUTULLI_URL')), require_env('TAUTULLI_API_KEY', os.getenv('TAUTULLI_API_KEY')), default_timeout=APP_STATE['timeout'])


def _emit(data: Any, pretty: bool) -> None:
    echo_json(data, pretty=pretty)


def _run(execute, *, pretty: bool) -> None:
    _emit(run_cli_command(None, execute, timeout=APP_STATE['timeout']), pretty)


def _run_write(build_request, execute, *, dry_run: bool, pretty: bool) -> None:
    _emit(run_cli_command(build_request, execute, timeout=APP_STATE['timeout'], dry_run=dry_run), pretty)


@app.command('call')
def call(cmd: str, args_json: str | None = typer.Option(None, '--args-json'), dry_run: bool = typer.Option(False, '--dry-run'), pretty: bool = typer.Option(False, '--pretty')) -> None:
    client = get_client()
    args = parse_json_option(args_json, '--args-json') or {}
    _run_write(lambda: client.build_call(cmd, **args), lambda timeout: client.call(cmd, timeout=timeout, **args), dry_run=dry_run, pretty=pretty)


@app.command('get_server_status')
def get_server_status(pretty: bool = typer.Option(False, '--pretty')) -> None:
    client = get_client()
    _run(lambda timeout: client.get_server_status(timeout=timeout), pretty=pretty)


@app.command('get_tautulli_info')
def get_tautulli_info(pretty: bool = typer.Option(False, '--pretty')) -> None:
    client = get_client()
    _run(lambda timeout: client.get_tautulli_info(timeout=timeout), pretty=pretty)


@app.command('get_status')
def get_status(pretty: bool = typer.Option(False, '--pretty')) -> None:
    client = get_client()
    _run(lambda timeout: client.get_status(timeout=timeout), pretty=pretty)


@app.command('get_activity')
def get_activity(pretty: bool = typer.Option(False, '--pretty')) -> None:
    client = get_client()
    _run(lambda timeout: client.get_activity(timeout=timeout), pretty=pretty)


@app.command('terminate_session')
def terminate_session(session_id: str, message: str | None = typer.Option(None, '--message'), dry_run: bool = typer.Option(False, '--dry-run'), pretty: bool = typer.Option(False, '--pretty')) -> None:
    client = get_client()
    _run_write(lambda: client.build_terminate_session(session_id, message=message), lambda timeout: client.terminate_session(session_id, message=message, timeout=timeout), dry_run=dry_run, pretty=pretty)


@app.command('get_history')
def get_history(page: int = typer.Option(1, '--page'), length: int = typer.Option(10, '--length'), search: str | None = typer.Option(None, '--search'), order_column: str = typer.Option('date', '--order-column'), order_dir: str = typer.Option('desc', '--order-dir'), pretty: bool = typer.Option(False, '--pretty')) -> None:
    client = get_client()
    _run(lambda timeout: client.get_history(page=page, length=length, search=search, order_column=order_column, order_dir=order_dir, timeout=timeout), pretty=pretty)


@app.command('get_libraries')
def get_libraries(pretty: bool = typer.Option(False, '--pretty')) -> None:
    client = get_client()
    _run(lambda timeout: client.get_libraries(timeout=timeout), pretty=pretty)


@app.command('get_library_user_stats')
def get_library_user_stats(section_id: int, pretty: bool = typer.Option(False, '--pretty')) -> None:
    client = get_client()
    _run(lambda timeout: client.get_library_user_stats(section_id, timeout=timeout), pretty=pretty)


@app.command('get_users')
def get_users(pretty: bool = typer.Option(False, '--pretty')) -> None:
    client = get_client()
    _run(lambda timeout: client.get_users(timeout=timeout), pretty=pretty)


@app.command('get_user_player_stats')
def get_user_player_stats(user_id: int, pretty: bool = typer.Option(False, '--pretty')) -> None:
    client = get_client()
    _run(lambda timeout: client.get_user_player_stats(user_id, timeout=timeout), pretty=pretty)


@app.command('get_user_watch_time_stats')
def get_user_watch_time_stats(user_id: int, pretty: bool = typer.Option(False, '--pretty')) -> None:
    client = get_client()
    _run(lambda timeout: client.get_user_watch_time_stats(user_id, timeout=timeout), pretty=pretty)


@app.command('get_metadata')
def get_metadata(rating_key: int, pretty: bool = typer.Option(False, '--pretty')) -> None:
    client = get_client()
    _run(lambda timeout: client.get_metadata(rating_key, timeout=timeout), pretty=pretty)


@app.command('search')
def search(query: str, limit: int = typer.Option(10, '--limit'), pretty: bool = typer.Option(False, '--pretty')) -> None:
    client = get_client()
    _run(lambda timeout: client.search(query, limit=limit, timeout=timeout), pretty=pretty)


@app.command('restart')
def restart(dry_run: bool = typer.Option(False, '--dry-run'), pretty: bool = typer.Option(False, '--pretty')) -> None:
    client = get_client()
    _run_write(lambda: client.build_restart(), lambda timeout: client.restart(timeout=timeout), dry_run=dry_run, pretty=pretty)


def main() -> None:
    run_app(app)


if __name__ == '__main__':
    main()
