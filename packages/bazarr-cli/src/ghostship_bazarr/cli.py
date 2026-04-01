from __future__ import annotations

import json
import os
import sys
from typing import Any

import typer

from .client import BazarrClient

app = typer.Typer(help="Bazarr CLI interface.", no_args_is_help=True)


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


def get_client() -> BazarrClient:
    base_url = os.getenv("BAZARR_URL")
    api_key = os.getenv("BAZARR_API_KEY")
    if not base_url or not api_key:
        print("Error: BAZARR_URL and BAZARR_API_KEY environment variables must be set.", file=sys.stderr)
        raise typer.Exit(code=1)
    return BazarrClient(base_url, api_key)


@app.command("request")
def request(method: str, path: str, param: list[str] = typer.Option([], "--param"), body_json: str | None = typer.Option(None, "--body-json"), pretty: bool = typer.Option(False, "--pretty")) -> None:
    echo_json(get_client().request(method, path, params=_parse_params(param) or None, json_data=_parse_json_option(body_json, "--body-json")), pretty=pretty)


@app.command("get_badges")
def get_badges(pretty: bool = typer.Option(False, "--pretty")) -> None:
    echo_json(get_client().get_badges(), pretty=pretty)


@app.command("get_episodes")
def get_episodes(series_id: int | None = typer.Option(None, "--series-id"), pretty: bool = typer.Option(False, "--pretty")) -> None:
    echo_json(get_client().get_episodes(series_id=series_id), pretty=pretty)


@app.command("get_wanted_episodes")
def get_wanted_episodes(pretty: bool = typer.Option(False, "--pretty")) -> None:
    echo_json(get_client().get_wanted_episodes(), pretty=pretty)


@app.command("get_movies")
def get_movies(pretty: bool = typer.Option(False, "--pretty")) -> None:
    echo_json(get_client().get_movies(), pretty=pretty)


@app.command("get_wanted_movies")
def get_wanted_movies(pretty: bool = typer.Option(False, "--pretty")) -> None:
    echo_json(get_client().get_wanted_movies(), pretty=pretty)


@app.command("get_series")
def get_series(pretty: bool = typer.Option(False, "--pretty")) -> None:
    echo_json(get_client().get_series(), pretty=pretty)


@app.command("get_providers")
def get_providers(pretty: bool = typer.Option(False, "--pretty")) -> None:
    echo_json(get_client().get_providers(), pretty=pretty)


@app.command("get_subtitles")
def get_subtitles(pretty: bool = typer.Option(False, "--pretty")) -> None:
    echo_json(get_client().get_subtitles(), pretty=pretty)


@app.command("get_system_health")
def get_system_health(pretty: bool = typer.Option(False, "--pretty")) -> None:
    echo_json(get_client().get_system_health(), pretty=pretty)


@app.command("get_system_jobs")
def get_system_jobs(pretty: bool = typer.Option(False, "--pretty")) -> None:
    echo_json(get_client().get_system_jobs(), pretty=pretty)


@app.command("get_system_tasks")
def get_system_tasks(pretty: bool = typer.Option(False, "--pretty")) -> None:
    echo_json(get_client().get_system_tasks(), pretty=pretty)


@app.command("get_system_status")
def get_system_status(pretty: bool = typer.Option(False, "--pretty")) -> None:
    echo_json(get_client().get_system_status(), pretty=pretty)


@app.command("search_subtitles_missing")
def search_subtitles_missing(pretty: bool = typer.Option(False, "--pretty")) -> None:
    echo_json(get_client().search_subtitles_missing(), pretty=pretty)


@app.command("get_episodes_history")
def get_episodes_history(pretty: bool = typer.Option(False, "--pretty")) -> None:
    echo_json(get_client().get_episodes_history(), pretty=pretty)


@app.command("get_movies_history")
def get_movies_history(pretty: bool = typer.Option(False, "--pretty")) -> None:
    echo_json(get_client().get_movies_history(), pretty=pretty)


@app.command("get_episodes_blacklist")
def get_episodes_blacklist(pretty: bool = typer.Option(False, "--pretty")) -> None:
    echo_json(get_client().get_episodes_blacklist(), pretty=pretty)


@app.command("get_movies_blacklist")
def get_movies_blacklist(pretty: bool = typer.Option(False, "--pretty")) -> None:
    echo_json(get_client().get_movies_blacklist(), pretty=pretty)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
