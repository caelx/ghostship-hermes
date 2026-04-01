from __future__ import annotations

import json
import os
from typing import Any

import typer

from .client import FlareSolverrClient

app = typer.Typer(help="FlareSolverr CLI interface.", no_args_is_help=True)


def echo_json(data: Any, pretty: bool = False) -> None:
    typer.echo(json.dumps(data, indent=2 if pretty else None))


def _parse_json_option(value: str | None, option_name: str) -> Any:
    if value is None:
        return None
    try:
        return json.loads(value)
    except json.JSONDecodeError as exc:
        raise typer.BadParameter(f"{option_name} must be valid JSON: {exc}") from exc


def get_client() -> FlareSolverrClient:
    base_url = os.getenv("FLARESOLVERR_URL")
    if not base_url:
        raise typer.Exit("FLARESOLVERR_URL environment variable must be set.")
    return FlareSolverrClient(base_url)


@app.command("command")
def command(cmd: str, params_json: str | None = typer.Option(None, "--params-json"), pretty: bool = typer.Option(False, "--pretty")) -> None:
    kwargs = _parse_json_option(params_json, "--params-json") or {}
    echo_json(get_client().command(cmd, **kwargs), pretty=pretty)


@app.command("request_get")
def request_get(url: str, session: str | None = typer.Option(None, "--session"), pretty: bool = typer.Option(False, "--pretty")) -> None:
    echo_json(get_client().request_get(url, session=session), pretty=pretty)


@app.command("request_post")
def request_post(url: str, post_data: str, session: str | None = typer.Option(None, "--session"), pretty: bool = typer.Option(False, "--pretty")) -> None:
    echo_json(get_client().request_post(url, post_data, session=session), pretty=pretty)


@app.command("sessions_create")
def sessions_create(session: str | None = typer.Option(None, "--session"), pretty: bool = typer.Option(False, "--pretty")) -> None:
    echo_json(get_client().sessions_create(session=session), pretty=pretty)


@app.command("sessions_list")
def sessions_list(pretty: bool = typer.Option(False, "--pretty")) -> None:
    echo_json(get_client().sessions_list(), pretty=pretty)


@app.command("sessions_destroy")
def sessions_destroy(session: str, pretty: bool = typer.Option(False, "--pretty")) -> None:
    echo_json(get_client().sessions_destroy(session), pretty=pretty)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
