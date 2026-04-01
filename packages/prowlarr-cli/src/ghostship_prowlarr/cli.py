from __future__ import annotations

import os
from typing import Any

import typer

from ghostship_cli_contract import DEFAULT_TIMEOUT, echo_json, handle_cli_error, parse_json_option, parse_params, require_env, run_app, run_cli_command

from .client import ProwlarrClient

app = typer.Typer(help="Prowlarr CLI interface.", no_args_is_help=True)
APP_STATE = {"timeout": DEFAULT_TIMEOUT}


@app.callback()
def app_callback(timeout: float = typer.Option(DEFAULT_TIMEOUT, "--timeout", help="Hard timeout in seconds for all API calls in this invocation.")) -> None:
    APP_STATE["timeout"] = timeout


def get_client() -> ProwlarrClient:
    return ProwlarrClient(require_env("PROWLARR_URL", os.getenv("PROWLARR_URL")), require_env("PROWLARR_API_KEY", os.getenv("PROWLARR_API_KEY")), default_timeout=APP_STATE["timeout"])


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
def get_status(pretty: bool = typer.Option(False, "--pretty")) -> None:
    _run(lambda: get_client().get_status(), pretty=pretty)


@app.command("get_indexers")
def get_indexers(indexer_id: int | None = None, pretty: bool = typer.Option(False, "--pretty")) -> None:
    _run(lambda: get_client().get_indexers(indexer_id), pretty=pretty)


@app.command("search")
def search(query: str, category_json: str | None = typer.Option(None, "--category-json", help="Optional JSON array of category ids"), pretty: bool = typer.Option(False, "--pretty")) -> None:
    categories = parse_json_option(category_json, "--category-json") if category_json else None
    _run(lambda: get_client().search(query, categories=categories), pretty=pretty)


@app.command("get_applications")
def get_applications(app_id: int | None = None, pretty: bool = typer.Option(False, "--pretty")) -> None:
    _run(lambda: get_client().get_applications(app_id), pretty=pretty)


@app.command("get_history")
def get_history(page: int = 1, page_size: int = 10, pretty: bool = typer.Option(False, "--pretty")) -> None:
    _run(lambda: get_client().get_history(page=page, page_size=page_size), pretty=pretty)


@app.command("get_indexer_stats")
def get_indexer_stats(pretty: bool = typer.Option(False, "--pretty")) -> None:
    _run(lambda: get_client().get_indexer_stats(), pretty=pretty)


@app.command("get_indexer_status")
def get_indexer_status(pretty: bool = typer.Option(False, "--pretty")) -> None:
    _run(lambda: get_client().get_indexer_status(), pretty=pretty)


@app.command("run_command")
def run_command(name: str, args: str | None = typer.Option(None, "--args", help="JSON object merged into the command payload"), dry_run: bool = typer.Option(False, "--dry-run", help="Print the request JSON and do not call the API."), pretty: bool = typer.Option(False, "--pretty")) -> None:
    kwargs = parse_json_option(args, "--args") or {}
    payload = {"name": name, **kwargs}
    _run_write(lambda client: lambda: client.build_request("POST", "command", json_data=payload, timeout=APP_STATE["timeout"]), lambda client: lambda timeout: client.run_command(name, timeout=timeout, **kwargs), dry_run=dry_run, pretty=pretty)


def main() -> None:
    run_app(app)


if __name__ == "__main__":
    main()
