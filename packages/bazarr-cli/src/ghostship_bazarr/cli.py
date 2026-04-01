from __future__ import annotations

import os
from typing import Any

import typer

from ghostship_cli_contract import DEFAULT_TIMEOUT, echo_json, handle_cli_error, parse_json_option, parse_params, require_env, run_app, run_cli_command

from .client import BazarrClient

app = typer.Typer(help="Bazarr CLI interface.", no_args_is_help=True)
APP_STATE = {"timeout": DEFAULT_TIMEOUT}


@app.callback()
def app_callback(timeout: float = typer.Option(DEFAULT_TIMEOUT, "--timeout", help="Hard timeout in seconds for all API calls in this invocation.")) -> None:
    APP_STATE["timeout"] = timeout


def get_client() -> BazarrClient:
    return BazarrClient(require_env("BAZARR_URL", os.getenv("BAZARR_URL")), require_env("BAZARR_API_KEY", os.getenv("BAZARR_API_KEY")), default_timeout=APP_STATE["timeout"])


def _emit(result: Any, *, pretty: bool) -> None:
    echo_json(result, pretty=pretty)


def _run(read_op, *, pretty: bool) -> None:
    try:
        _emit(read_op(), pretty=pretty)
    except Exception as exc:
        handle_cli_error(exc)


def _run_write(build_request, execute, *, dry_run: bool, pretty: bool) -> None:
    try:
        client = get_client()
        result = run_cli_command(build_request(client), execute(client), timeout=APP_STATE["timeout"], dry_run=dry_run)
        _emit(result, pretty=pretty)
    except Exception as exc:
        handle_cli_error(exc)


@app.command("request")
def request(method: str, path: str, param: list[str] = typer.Option([], "--param"), body_json: str | None = typer.Option(None, "--body-json"), dry_run: bool = typer.Option(False, "--dry-run"), pretty: bool = typer.Option(False, "--pretty")) -> None:
    params = parse_params(param) or None
    payload = parse_json_option(body_json, "--body-json")
    _run_write(lambda client: lambda: client.build_request(method, path, params=params, json_data=payload, timeout=APP_STATE["timeout"]), lambda client: lambda timeout: client.request(method, path, params=params, json_data=payload, timeout=timeout), dry_run=dry_run, pretty=pretty)


@app.command("get_badges")
def get_badges(pretty: bool = typer.Option(False, "--pretty")) -> None:
    _run(lambda: get_client().get_badges(), pretty=pretty)


@app.command("get_episodes")
def get_episodes(series_id: int | None = None, pretty: bool = typer.Option(False, "--pretty")) -> None:
    _run(lambda: get_client().get_episodes(series_id), pretty=pretty)


@app.command("get_wanted_episodes")
def get_wanted_episodes(pretty: bool = typer.Option(False, "--pretty")) -> None:
    _run(lambda: get_client().get_wanted_episodes(), pretty=pretty)


@app.command("get_movies")
def get_movies(pretty: bool = typer.Option(False, "--pretty")) -> None:
    _run(lambda: get_client().get_movies(), pretty=pretty)


@app.command("get_wanted_movies")
def get_wanted_movies(pretty: bool = typer.Option(False, "--pretty")) -> None:
    _run(lambda: get_client().get_wanted_movies(), pretty=pretty)


@app.command("get_series")
def get_series(pretty: bool = typer.Option(False, "--pretty")) -> None:
    _run(lambda: get_client().get_series(), pretty=pretty)


@app.command("get_providers")
def get_providers(pretty: bool = typer.Option(False, "--pretty")) -> None:
    _run(lambda: get_client().get_providers(), pretty=pretty)


@app.command("get_subtitles")
def get_subtitles(pretty: bool = typer.Option(False, "--pretty")) -> None:
    _run(lambda: get_client().get_subtitles(), pretty=pretty)


@app.command("get_system_health")
def get_system_health(pretty: bool = typer.Option(False, "--pretty")) -> None:
    _run(lambda: get_client().get_system_health(), pretty=pretty)


@app.command("get_system_jobs")
def get_system_jobs(pretty: bool = typer.Option(False, "--pretty")) -> None:
    _run(lambda: get_client().get_system_jobs(), pretty=pretty)


@app.command("get_system_tasks")
def get_system_tasks(pretty: bool = typer.Option(False, "--pretty")) -> None:
    _run(lambda: get_client().get_system_tasks(), pretty=pretty)


@app.command("get_system_status")
def get_system_status(pretty: bool = typer.Option(False, "--pretty")) -> None:
    _run(lambda: get_client().get_system_status(), pretty=pretty)


@app.command("search_subtitles_missing")
def search_subtitles_missing(dry_run: bool = typer.Option(False, "--dry-run"), pretty: bool = typer.Option(False, "--pretty")) -> None:
    _run_write(lambda client: lambda: client.build_request("POST", "subtitles/search/missing", timeout=APP_STATE["timeout"]), lambda client: lambda timeout: client.search_subtitles_missing(timeout=timeout), dry_run=dry_run, pretty=pretty)


@app.command("get_episodes_history")
def get_episodes_history(pretty: bool = typer.Option(False, "--pretty")) -> None:
    _run(lambda: get_client().get_episodes_history(), pretty=pretty)


@app.command("get_movies_history")
def get_movies_history(pretty: bool = typer.Option(False, "--pretty")) -> None:
    _run(lambda: get_client().get_movies_history(), pretty=pretty)


@app.command("get_episodes_blacklist")
def get_episodes_blacklist(pretty: bool = typer.Option(False, "--pretty")) -> None:
    _run(lambda: get_client().get_episodes_blacklist(), pretty=pretty)


@app.command("get_movies_blacklist")
def get_movies_blacklist(pretty: bool = typer.Option(False, "--pretty")) -> None:
    _run(lambda: get_client().get_movies_blacklist(), pretty=pretty)


def main() -> None:
    run_app(app)


if __name__ == "__main__":
    main()
