from __future__ import annotations

import os
from typing import Any

import typer

from ghostship_cli_contract import DEFAULT_TIMEOUT, echo_json, parse_json_option, parse_params, require_env, run_app, run_cli_command

from .client import GrimmoryClient

HELP_TEXT = """Grimmory CLI interface.

Auth:
- Set GRIMMORY_URL.
- Preferred: set GRIMMORY_USERNAME and GRIMMORY_PASSWORD.
- Optional override: set GRIMMORY_TOKEN.
"""

app = typer.Typer(help=HELP_TEXT, no_args_is_help=True)
APP_STATE = {'timeout': DEFAULT_TIMEOUT}


@app.callback()
def app_callback(timeout: float = typer.Option(DEFAULT_TIMEOUT, '--timeout', help='Hard timeout in seconds for all API calls in this invocation.')) -> None:
    APP_STATE['timeout'] = timeout


def get_client() -> GrimmoryClient:
    return GrimmoryClient(require_env('GRIMMORY_URL', os.getenv('GRIMMORY_URL')), token=os.getenv('GRIMMORY_TOKEN'), username=os.getenv('GRIMMORY_USERNAME'), password=os.getenv('GRIMMORY_PASSWORD'), default_timeout=APP_STATE['timeout'])


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


@app.command('get_books')
def get_books(page: int = typer.Option(0, '--page'), size: int = typer.Option(20, '--size'), library_id: int | None = typer.Option(None, '--library-id'), pretty: bool = typer.Option(False, '--pretty')) -> None:
    client = get_client()
    _run(lambda timeout: client.get_books(page=page, size=size, library_id=library_id, timeout=timeout), pretty=pretty)


@app.command('get_book')
def get_book(book_id: int, pretty: bool = typer.Option(False, '--pretty')) -> None:
    client = get_client()
    _run(lambda timeout: client.get_book(book_id, timeout=timeout), pretty=pretty)


@app.command('download_book')
def download_book(book_id: int, pretty: bool = typer.Option(False, '--pretty')) -> None:
    client = get_client()
    _run(lambda timeout: client.download_book(book_id, timeout=timeout), pretty=pretty)


@app.command('get_libraries')
def get_libraries(pretty: bool = typer.Option(False, '--pretty')) -> None:
    client = get_client()
    _run(lambda timeout: client.get_libraries(timeout=timeout), pretty=pretty)


@app.command('get_library')
def get_library(library_id: int, pretty: bool = typer.Option(False, '--pretty')) -> None:
    client = get_client()
    _run(lambda timeout: client.get_library(library_id, timeout=timeout), pretty=pretty)


@app.command('scan_libraries')
def scan_libraries(dry_run: bool = typer.Option(False, '--dry-run'), pretty: bool = typer.Option(False, '--pretty')) -> None:
    client = get_client()
    _run_write(lambda: client.build_scan_libraries(), lambda timeout: client.scan_libraries(timeout=timeout), dry_run=dry_run, pretty=pretty)


@app.command('refresh_library')
def refresh_library(library_id: int, dry_run: bool = typer.Option(False, '--dry-run'), pretty: bool = typer.Option(False, '--pretty')) -> None:
    client = get_client()
    _run_write(lambda: client.build_refresh_library(library_id), lambda timeout: client.refresh_library(library_id, timeout=timeout), dry_run=dry_run, pretty=pretty)


@app.command('get_authors')
def get_authors(page: int = typer.Option(0, '--page'), size: int = typer.Option(20, '--size'), pretty: bool = typer.Option(False, '--pretty')) -> None:
    client = get_client()
    _run(lambda timeout: client.get_authors(page=page, size=size, timeout=timeout), pretty=pretty)


@app.command('get_author')
def get_author(author_id: int, pretty: bool = typer.Option(False, '--pretty')) -> None:
    client = get_client()
    _run(lambda timeout: client.get_author(author_id, timeout=timeout), pretty=pretty)


@app.command('get_shelves')
def get_shelves(pretty: bool = typer.Option(False, '--pretty')) -> None:
    client = get_client()
    _run(lambda timeout: client.get_shelves(timeout=timeout), pretty=pretty)


@app.command('get_shelf_books')
def get_shelf_books(shelf_id: int, pretty: bool = typer.Option(False, '--pretty')) -> None:
    client = get_client()
    _run(lambda timeout: client.get_shelf_books(shelf_id, timeout=timeout), pretty=pretty)


@app.command('get_tasks')
def get_tasks(pretty: bool = typer.Option(False, '--pretty')) -> None:
    client = get_client()
    _run(lambda timeout: client.get_tasks(timeout=timeout), pretty=pretty)


@app.command('cancel_task')
def cancel_task(task_id: str, dry_run: bool = typer.Option(False, '--dry-run'), pretty: bool = typer.Option(False, '--pretty')) -> None:
    client = get_client()
    _run_write(lambda: client.build_cancel_task(task_id), lambda timeout: client.cancel_task(task_id, timeout=timeout), dry_run=dry_run, pretty=pretty)


@app.command('get_version')
def get_version(pretty: bool = typer.Option(False, '--pretty')) -> None:
    client = get_client()
    _run(lambda timeout: client.get_version(timeout=timeout), pretty=pretty)


def main() -> None:
    run_app(app)


if __name__ == '__main__':
    main()
