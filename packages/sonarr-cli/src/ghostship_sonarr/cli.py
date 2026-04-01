from __future__ import annotations

import os
from typing import Any

import typer

from ghostship_cli_contract import DEFAULT_TIMEOUT, echo_json, handle_cli_error, parse_json_option, parse_params, require_env, run_app, run_cli_command

from .client import SonarrClient

app = typer.Typer(help="Sonarr CLI interface.", no_args_is_help=True)
APP_STATE = {"timeout": DEFAULT_TIMEOUT}


@app.callback()
def app_callback(timeout: float = typer.Option(DEFAULT_TIMEOUT, "--timeout", help="Hard timeout in seconds for all API calls in this invocation.")) -> None:
    APP_STATE["timeout"] = timeout


def get_client() -> SonarrClient:
    base_url = require_env("SONARR_URL", os.getenv("SONARR_URL"))
    api_key = require_env("SONARR_API_KEY", os.getenv("SONARR_API_KEY"))
    return SonarrClient(base_url, api_key, default_timeout=APP_STATE["timeout"])


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
def request(
    method: str,
    path: str,
    param: list[str] = typer.Option([], "--param", help="Repeat key=value query parameters."),
    body_json: str | None = typer.Option(None, "--body-json", help="Optional JSON request body."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Print the request JSON and do not call the API."),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output"),
) -> None:
    params = parse_params(param) or None
    payload = parse_json_option(body_json, "--body-json")
    _run_write(
        lambda client: lambda: client.build_request(method, path, params=params, json_data=payload, timeout=APP_STATE["timeout"]),
        lambda client: lambda timeout: client.request(method, path, params=params, json_data=payload, timeout=timeout),
        dry_run=dry_run,
        pretty=pretty,
    )


@app.command("get_status")
def get_status(pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output")) -> None:
    _run(lambda: get_client().get_status(), pretty=pretty)


@app.command("get_series")
def get_series(series_id: int | None = None, pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output")) -> None:
    _run(lambda: get_client().get_series(series_id), pretty=pretty)


@app.command("lookup_series")
def lookup_series(term: str, pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output")) -> None:
    _run(lambda: get_client().lookup_series(term), pretty=pretty)


@app.command("add_series")
def add_series(body_json: str = typer.Option(..., "--body-json", help="JSON request body for POST /series"), dry_run: bool = typer.Option(False, "--dry-run", help="Print the request JSON and do not call the API."), pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output")) -> None:
    payload = parse_json_option(body_json, "--body-json")
    _run_write(lambda client: lambda: client.build_request("POST", "series", json_data=payload, timeout=APP_STATE["timeout"]), lambda client: lambda timeout: client.add_series(payload, timeout=timeout), dry_run=dry_run, pretty=pretty)


@app.command("update_series")
def update_series(body_json: str = typer.Option(..., "--body-json", help="JSON request body for PUT /series"), dry_run: bool = typer.Option(False, "--dry-run", help="Print the request JSON and do not call the API."), pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output")) -> None:
    payload = parse_json_option(body_json, "--body-json")
    _run_write(lambda client: lambda: client.build_request("PUT", "series", json_data=payload, timeout=APP_STATE["timeout"]), lambda client: lambda timeout: client.update_series(payload, timeout=timeout), dry_run=dry_run, pretty=pretty)


@app.command("delete_series")
def delete_series(series_id: int, delete_files: bool = typer.Option(False, "--delete-files"), dry_run: bool = typer.Option(False, "--dry-run", help="Print the request JSON and do not call the API."), pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output")) -> None:
    params = {"deleteFiles": str(delete_files).lower()}
    _run_write(lambda client: lambda: client.build_request("DELETE", f"series/{series_id}", params=params, timeout=APP_STATE["timeout"]), lambda client: lambda timeout: client.delete_series(series_id, delete_files=delete_files, timeout=timeout), dry_run=dry_run, pretty=pretty)


@app.command("get_episodes")
def get_episodes(series_id: int, pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output")) -> None:
    _run(lambda: get_client().get_episodes(series_id), pretty=pretty)


@app.command("get_episode")
def get_episode(episode_id: int, pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output")) -> None:
    _run(lambda: get_client().get_episode(episode_id), pretty=pretty)


@app.command("update_episode")
def update_episode(body_json: str = typer.Option(..., "--body-json", help="JSON request body for PUT /episode"), dry_run: bool = typer.Option(False, "--dry-run", help="Print the request JSON and do not call the API."), pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output")) -> None:
    payload = parse_json_option(body_json, "--body-json")
    _run_write(lambda client: lambda: client.build_request("PUT", "episode", json_data=payload, timeout=APP_STATE["timeout"]), lambda client: lambda timeout: client.update_episode(payload, timeout=timeout), dry_run=dry_run, pretty=pretty)


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
def get_wanted_missing(page: int = 1, page_size: int = 10, sort_key: str = "airDateUtc", sort_direction: str = "descending", pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output")) -> None:
    _run(lambda: get_client().get_wanted_missing(page=page, page_size=page_size, sort_key=sort_key, sort_direction=sort_direction), pretty=pretty)


@app.command("get_wanted_cutoff")
def get_wanted_cutoff(page: int = 1, page_size: int = 10, pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output")) -> None:
    _run(lambda: get_client().get_wanted_cutoff(page=page, page_size=page_size), pretty=pretty)


@app.command("get_blocklist")
def get_blocklist(page: int = 1, page_size: int = 10, pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output")) -> None:
    _run(lambda: get_client().get_blocklist(page=page, page_size=page_size), pretty=pretty)


@app.command("get_blocklist_series")
def get_blocklist_series(page: int = 1, page_size: int = 10, pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output")) -> None:
    _run(lambda: get_client().get_blocklist_series(page=page, page_size=page_size), pretty=pretty)


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
