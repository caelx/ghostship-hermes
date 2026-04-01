from __future__ import annotations

import os
from typing import Any

import typer

from ghostship_cli_contract import DEFAULT_TIMEOUT, echo_json, parse_json_option, run_app, run_cli_command

from .client import FlareSolverrClient

app = typer.Typer(help='FlareSolverr CLI interface.', no_args_is_help=True)
APP_STATE = {'timeout': DEFAULT_TIMEOUT}


@app.callback()
def app_callback(timeout: float = typer.Option(DEFAULT_TIMEOUT, '--timeout', help='Hard timeout in seconds for all API calls in this invocation.')) -> None:
    APP_STATE['timeout'] = timeout


def get_client() -> FlareSolverrClient:
    base_url = os.getenv('FLARESOLVERR_URL', 'http://localhost:8191')
    return FlareSolverrClient(base_url, default_timeout=APP_STATE['timeout'])


def _emit(data: Any, pretty: bool) -> None:
    echo_json(data, pretty=pretty)


def _run(execute, *, pretty: bool) -> None:
    _emit(run_cli_command(None, execute, timeout=APP_STATE['timeout']), pretty)


def _run_write(build_request, execute, *, dry_run: bool, pretty: bool) -> None:
    _emit(run_cli_command(build_request, execute, timeout=APP_STATE['timeout'], dry_run=dry_run), pretty)


@app.command('command')
def command(cmd: str, args_json: str | None = typer.Option(None, '--args-json', help='Optional JSON object merged into the request payload.'), dry_run: bool = typer.Option(False, '--dry-run', help='Print the request JSON and do not call the API.'), pretty: bool = typer.Option(False, '--pretty')) -> None:
    client = get_client()
    args = parse_json_option(args_json, '--args-json') or {}
    _run_write(lambda: client.build_command(cmd, **args), lambda timeout: client.command(cmd, timeout=timeout, **args), dry_run=dry_run, pretty=pretty)


@app.command('request_get')
def request_get(url: str, session: str | None = typer.Option(None, '--session'), pretty: bool = typer.Option(False, '--pretty')) -> None:
    client = get_client()
    _run(lambda timeout: client.request_get(url, session=session, timeout=timeout), pretty=pretty)


@app.command('request_post')
def request_post(url: str, post_data: str, session: str | None = typer.Option(None, '--session'), dry_run: bool = typer.Option(False, '--dry-run', help='Print the request JSON and do not call the API.'), pretty: bool = typer.Option(False, '--pretty')) -> None:
    client = get_client()
    _run_write(lambda: client.build_request_post(url, post_data, session=session), lambda timeout: client.request_post(url, post_data, session=session, timeout=timeout), dry_run=dry_run, pretty=pretty)


@app.command('sessions_create')
def sessions_create(session: str | None = typer.Option(None, '--session'), dry_run: bool = typer.Option(False, '--dry-run', help='Print the request JSON and do not call the API.'), pretty: bool = typer.Option(False, '--pretty')) -> None:
    client = get_client()
    _run_write(lambda: client.build_sessions_create(session=session), lambda timeout: client.sessions_create(session=session, timeout=timeout), dry_run=dry_run, pretty=pretty)


@app.command('sessions_list')
def sessions_list(pretty: bool = typer.Option(False, '--pretty')) -> None:
    client = get_client()
    _run(lambda timeout: client.sessions_list(timeout=timeout), pretty=pretty)


@app.command('sessions_destroy')
def sessions_destroy(session: str, dry_run: bool = typer.Option(False, '--dry-run', help='Print the request JSON and do not call the API.'), pretty: bool = typer.Option(False, '--pretty')) -> None:
    client = get_client()
    _run_write(lambda: client.build_sessions_destroy(session), lambda timeout: client.sessions_destroy(session, timeout=timeout), dry_run=dry_run, pretty=pretty)


def main() -> None:
    run_app(app)


if __name__ == '__main__':
    main()
