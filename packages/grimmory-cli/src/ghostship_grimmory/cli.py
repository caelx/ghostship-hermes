from __future__ import annotations

import json
import os
import sys
from typing import Any

import typer

from .client import GrimmoryClient

HELP_TEXT = """Grimmory CLI interface.

Auth:
- Set GRIMMORY_URL.
- Preferred: set GRIMMORY_USERNAME and GRIMMORY_PASSWORD.
- Optional override: set GRIMMORY_TOKEN.
"""

app = typer.Typer(help=HELP_TEXT, no_args_is_help=True)


def echo_json(data: Any, pretty: bool = False) -> None:
    typer.echo(json.dumps(data, indent=2 if pretty else None))


def _parse_json_option(value: str | None, option_name: str) -> Any:
    if value is None:
        return None
    try:
        return json.loads(value)
    except json.JSONDecodeError as exc:
        raise typer.BadParameter(f"{option_name} must be valid JSON: {exc}") from exc


def _parse_params(values: list[str]) -> dict[str, str]:
    params: dict[str, str] = {}
    for value in values:
        if "=" not in value:
            raise typer.BadParameter(f"parameter must use key=value form: {value}")
        key, raw = value.split("=", 1)
        params[key] = raw
    return params


def get_client() -> GrimmoryClient:
    base_url = os.getenv("GRIMMORY_URL")
    token = os.getenv("GRIMMORY_TOKEN")
    username = os.getenv("GRIMMORY_USERNAME")
    password = os.getenv("GRIMMORY_PASSWORD")
    if not base_url:
        print("Error: GRIMMORY_URL must be set.", file=sys.stderr)
        raise typer.Exit(code=1)
    if not token and not (username and password):
        print("Error: set GRIMMORY_TOKEN or GRIMMORY_USERNAME and GRIMMORY_PASSWORD.", file=sys.stderr)
        raise typer.Exit(code=1)
    return GrimmoryClient(base_url, token=token, username=username, password=password)


@app.command("request")
def request(method: str, path: str, param: list[str] = typer.Option([], "--param"), body_json: str | None = typer.Option(None, "--body-json"), pretty: bool = typer.Option(False, "--pretty")) -> None:
    echo_json(get_client().request(method, path, params=_parse_params(param) or None, json_data=_parse_json_option(body_json, "--body-json")), pretty=pretty)


@app.command("get_books")
def get_books(page: int = typer.Option(0, "--page"), size: int = typer.Option(20, "--size"), library_id: int | None = typer.Option(None, "--library-id"), pretty: bool = typer.Option(False, "--pretty")) -> None:
    echo_json(get_client().get_books(page=page, size=size, library_id=library_id), pretty=pretty)


@app.command("get_book")
def get_book(book_id: int, pretty: bool = typer.Option(False, "--pretty")) -> None:
    echo_json(get_client().get_book(book_id), pretty=pretty)


@app.command("download_book")
def download_book(book_id: int, pretty: bool = typer.Option(False, "--pretty")) -> None:
    echo_json(get_client().download_book(book_id), pretty=pretty)


@app.command("get_libraries")
def get_libraries(pretty: bool = typer.Option(False, "--pretty")) -> None:
    echo_json(get_client().get_libraries(), pretty=pretty)


@app.command("get_library")
def get_library(library_id: int, pretty: bool = typer.Option(False, "--pretty")) -> None:
    echo_json(get_client().get_library(library_id), pretty=pretty)


@app.command("scan_libraries")
def scan_libraries(pretty: bool = typer.Option(False, "--pretty")) -> None:
    echo_json(get_client().scan_libraries(), pretty=pretty)


@app.command("refresh_library")
def refresh_library(library_id: int, pretty: bool = typer.Option(False, "--pretty")) -> None:
    echo_json(get_client().refresh_library(library_id), pretty=pretty)


@app.command("get_authors")
def get_authors(page: int = typer.Option(0, "--page"), size: int = typer.Option(20, "--size"), pretty: bool = typer.Option(False, "--pretty")) -> None:
    echo_json(get_client().get_authors(page=page, size=size), pretty=pretty)


@app.command("get_author")
def get_author(author_id: int, pretty: bool = typer.Option(False, "--pretty")) -> None:
    echo_json(get_client().get_author(author_id), pretty=pretty)


@app.command("get_shelves")
def get_shelves(pretty: bool = typer.Option(False, "--pretty")) -> None:
    echo_json(get_client().get_shelves(), pretty=pretty)


@app.command("get_shelf_books")
def get_shelf_books(shelf_id: int, pretty: bool = typer.Option(False, "--pretty")) -> None:
    echo_json(get_client().get_shelf_books(shelf_id), pretty=pretty)


@app.command("get_tasks")
def get_tasks(pretty: bool = typer.Option(False, "--pretty")) -> None:
    echo_json(get_client().get_tasks(), pretty=pretty)


@app.command("cancel_task")
def cancel_task(task_id: str, pretty: bool = typer.Option(False, "--pretty")) -> None:
    echo_json(get_client().cancel_task(task_id), pretty=pretty)


@app.command("get_version")
def get_version(pretty: bool = typer.Option(False, "--pretty")) -> None:
    echo_json(get_client().get_version(), pretty=pretty)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
