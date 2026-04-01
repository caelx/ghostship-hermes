from __future__ import annotations

import os
from typing import Any

import typer

from ghostship_cli_contract import DEFAULT_TIMEOUT, echo_json, handle_cli_error, parse_json_option, parse_params, require_env, run_app, run_cli_command

from .client import RadarrClient

app = typer.Typer(help="Radarr CLI interface.", no_args_is_help=True)
APP_STATE = {"timeout": DEFAULT_TIMEOUT}


@app.callback()
def app_callback(timeout: float = typer.Option(DEFAULT_TIMEOUT, "--timeout", help="Hard timeout in seconds for all API calls in this invocation.")) -> None:
    APP_STATE["timeout"] = timeout


def get_client() -> RadarrClient:
    return RadarrClient(require_env("RADARR_URL", os.getenv("RADARR_URL")), require_env("RADARR_API_KEY", os.getenv("RADARR_API_KEY")), default_timeout=APP_STATE["timeout"])


def _emit(result: Any, *, pretty: bool) -> None:
    echo_json(result, pretty=pretty)


def _run(read_op, *, pretty: bool) -> None:
    try:
        _emit(read_op(), pretty=pretty)
    except Exception as exc:  # pragma: no cover
        handle_cli_error(exc)


def _run_write(build_request, execute, *, dry_run: bool, pretty: bool) -> None:
    try:
        client = get_client()
        result = run_cli_command(build_request(client), execute(client), timeout=APP_STATE["timeout"], dry_run=dry_run)
        _emit(result, pretty=pretty)
    except Exception as exc:  # pragma: no cover
        handle_cli_error(exc)


@app.command("request")
def request(method: str, path: str, param: list[str] = typer.Option([], "--param", help="Repeat key=value query parameters."), body_json: str | None = typer.Option(None, "--body-json", help="Optional JSON request body."), dry_run: bool = typer.Option(False, "--dry-run", help="Print the request JSON and do not call the API."), pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output")) -> None:
    params = parse_params(param) or None
    payload = parse_json_option(body_json, "--body-json")
    _run_write(lambda client: lambda: client.build_request(method, path, params=params, json_data=payload, timeout=APP_STATE["timeout"]), lambda client: lambda timeout: client.request(method, path, params=params, json_data=payload, timeout=timeout), dry_run=dry_run, pretty=pretty)


@app.command("get_status")
def get_status(pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output")) -> None:
    _run(lambda: get_client().get_status(), pretty=pretty)


@app.command("get_movies")
def get_movies(movie_id: int | None = None, pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output")) -> None:
    _run(lambda: get_client().get_movies(movie_id), pretty=pretty)


@app.command("lookup_movie")
def lookup_movie(term: str, pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output")) -> None:
    _run(lambda: get_client().lookup_movie(term), pretty=pretty)


@app.command("add_movie")
def add_movie(body_json: str = typer.Option(..., "--body-json", help="JSON request body for POST /movie"), dry_run: bool = typer.Option(False, "--dry-run", help="Print the request JSON and do not call the API."), pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output")) -> None:
    payload = parse_json_option(body_json, "--body-json")
    _run_write(lambda client: lambda: client.build_request("POST", "movie", json_data=payload, timeout=APP_STATE["timeout"]), lambda client: lambda timeout: client.add_movie(payload, timeout=timeout), dry_run=dry_run, pretty=pretty)


@app.command("update_movie")
def update_movie(body_json: str = typer.Option(..., "--body-json", help="JSON request body for PUT /movie"), dry_run: bool = typer.Option(False, "--dry-run", help="Print the request JSON and do not call the API."), pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output")) -> None:
    payload = parse_json_option(body_json, "--body-json")
    _run_write(lambda client: lambda: client.build_request("PUT", "movie", json_data=payload, timeout=APP_STATE["timeout"]), lambda client: lambda timeout: client.update_movie(payload, timeout=timeout), dry_run=dry_run, pretty=pretty)


@app.command("delete_movie")
def delete_movie(movie_id: int, delete_files: bool = typer.Option(False, "--delete-files"), dry_run: bool = typer.Option(False, "--dry-run", help="Print the request JSON and do not call the API."), pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output")) -> None:
    params = {"deleteFiles": str(delete_files).lower()}
    _run_write(lambda client: lambda: client.build_request("DELETE", f"movie/{movie_id}", params=params, timeout=APP_STATE["timeout"]), lambda client: lambda timeout: client.delete_movie(movie_id, delete_files=delete_files, timeout=timeout), dry_run=dry_run, pretty=pretty)


@app.command("get_commands")
def get_commands(pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output")) -> None:
    _run(lambda: get_client().get_commands(), pretty=pretty)


@app.command("run_command")
def run_command(name: str, args: str | None = typer.Option(None, "--args", help="JSON object merged into the command payload"), dry_run: bool = typer.Option(False, "--dry-run", help="Print the request JSON and do not call the API."), pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output")) -> None:
    kwargs = parse_json_option(args, "--args") or {}
    payload = {"name": name, **kwargs}
    _run_write(lambda client: lambda: client.build_request("POST", "command", json_data=payload, timeout=APP_STATE["timeout"]), lambda client: lambda timeout: client.run_command(name, timeout=timeout, **kwargs), dry_run=dry_run, pretty=pretty)


@app.command("get_queue")
def get_queue(page: int = 1, page_size: int = 10, sort_key: str = "timeleft", sort_direction: str = "ascending", pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output")) -> None:
    _run(lambda: get_client().get_queue(page=page, page_size=page_size, sort_key=sort_key, sort_direction=sort_direction), pretty=pretty)


@app.command("get_history")
def get_history(page: int = 1, page_size: int = 10, sort_key: str = "date", sort_direction: str = "descending", pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output")) -> None:
    _run(lambda: get_client().get_history(page=page, page_size=page_size, sort_key=sort_key, sort_direction=sort_direction), pretty=pretty)


@app.command("get_wanted_missing")
def get_wanted_missing(page: int = 1, page_size: int = 10, sort_key: str = "releaseDate", sort_direction: str = "descending", pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output")) -> None:
    _run(lambda: get_client().get_wanted_missing(page=page, page_size=page_size, sort_key=sort_key, sort_direction=sort_direction), pretty=pretty)


@app.command("get_wanted_cutoff")
def get_wanted_cutoff(page: int = 1, page_size: int = 10, pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output")) -> None:
    _run(lambda: get_client().get_wanted_cutoff(page=page, page_size=page_size), pretty=pretty)


@app.command("get_blocklist")
def get_blocklist(page: int = 1, page_size: int = 10, pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output")) -> None:
    _run(lambda: get_client().get_blocklist(page=page, page_size=page_size), pretty=pretty)


@app.command("get_blocklist_movie")
def get_blocklist_movie(page: int = 1, page_size: int = 10, pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output")) -> None:
    _run(lambda: get_client().get_blocklist_movie(page=page, page_size=page_size), pretty=pretty)


@app.command("get_tags")
def get_tags(pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output")) -> None:
    _run(lambda: get_client().get_tags(), pretty=pretty)


@app.command("get_root_folders")
def get_root_folders(pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output")) -> None:
    _run(lambda: get_client().get_root_folders(), pretty=pretty)


@app.command("get_quality_profiles")
def get_quality_profiles(pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output")) -> None:
    _run(lambda: get_client().get_quality_profiles(), pretty=pretty)


def main() -> None:
    run_app(app)


if __name__ == "__main__":
    main()
