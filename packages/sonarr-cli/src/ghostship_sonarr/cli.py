from __future__ import annotations

import json
import os
import sys
from typing import Any

import typer

from .client import SonarrClient

app = typer.Typer(help="Sonarr CLI interface.", no_args_is_help=True)


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


def get_client() -> SonarrClient:
    base_url = os.getenv("SONARR_URL")
    api_key = os.getenv("SONARR_API_KEY")
    if not base_url or not api_key:
        print(
            "Error: SONARR_URL and SONARR_API_KEY environment variables must be set.",
            file=sys.stderr,
        )
        raise typer.Exit(code=1)
    return SonarrClient(base_url, api_key)


@app.command("request")
def request(
    method: str,
    path: str,
    param: list[str] = typer.Option([], "--param", help="Repeat key=value query parameters."),
    body_json: str | None = typer.Option(None, "--body-json", help="Optional JSON request body."),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output"),
) -> None:
    echo_json(
        get_client().request(
            method,
            path,
            params=_parse_params(param) or None,
            json_data=_parse_json_option(body_json, "--body-json"),
        ),
        pretty=pretty,
    )


@app.command("get_status")
def get_status(pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output")) -> None:
    echo_json(get_client().get_status(), pretty=pretty)


@app.command("get_series")
def get_series(series_id: int | None = None, pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output")) -> None:
    echo_json(get_client().get_series(series_id), pretty=pretty)


@app.command("lookup_series")
def lookup_series(term: str, pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output")) -> None:
    echo_json(get_client().lookup_series(term), pretty=pretty)


@app.command("add_series")
def add_series(body_json: str = typer.Option(..., "--body-json", help="JSON request body for POST /series"), pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output")) -> None:
    echo_json(get_client().add_series(_parse_json_option(body_json, "--body-json")), pretty=pretty)


@app.command("update_series")
def update_series(body_json: str = typer.Option(..., "--body-json", help="JSON request body for PUT /series"), pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output")) -> None:
    echo_json(get_client().update_series(_parse_json_option(body_json, "--body-json")), pretty=pretty)


@app.command("delete_series")
def delete_series(series_id: int, delete_files: bool = typer.Option(False, "--delete-files"), pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output")) -> None:
    echo_json(get_client().delete_series(series_id, delete_files=delete_files), pretty=pretty)


@app.command("get_episodes")
def get_episodes(series_id: int, pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output")) -> None:
    echo_json(get_client().get_episodes(series_id), pretty=pretty)


@app.command("get_episode")
def get_episode(episode_id: int, pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output")) -> None:
    echo_json(get_client().get_episode(episode_id), pretty=pretty)


@app.command("update_episode")
def update_episode(body_json: str = typer.Option(..., "--body-json", help="JSON request body for PUT /episode"), pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output")) -> None:
    echo_json(get_client().update_episode(_parse_json_option(body_json, "--body-json")), pretty=pretty)


@app.command("get_commands")
def get_commands(pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output")) -> None:
    echo_json(get_client().get_commands(), pretty=pretty)


@app.command("run_command")
def run_command(name: str, args: str | None = typer.Option(None, "--args", help="JSON object merged into the command payload"), pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output")) -> None:
    kwargs = _parse_json_option(args, "--args") or {}
    echo_json(get_client().run_command(name, **kwargs), pretty=pretty)


@app.command("get_queue")
def get_queue(page: int = 1, page_size: int = 10, sort_key: str = "timeleft", sort_direction: str = "ascending", pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output")) -> None:
    echo_json(get_client().get_queue(page=page, page_size=page_size, sort_key=sort_key, sort_direction=sort_direction), pretty=pretty)


@app.command("get_history")
def get_history(page: int = 1, page_size: int = 10, sort_key: str = "date", sort_direction: str = "descending", pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output")) -> None:
    echo_json(get_client().get_history(page=page, page_size=page_size, sort_key=sort_key, sort_direction=sort_direction), pretty=pretty)


@app.command("get_wanted_missing")
def get_wanted_missing(page: int = 1, page_size: int = 10, sort_key: str = "airDateUtc", sort_direction: str = "descending", pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output")) -> None:
    echo_json(get_client().get_wanted_missing(page=page, page_size=page_size, sort_key=sort_key, sort_direction=sort_direction), pretty=pretty)


@app.command("get_wanted_cutoff")
def get_wanted_cutoff(page: int = 1, page_size: int = 10, pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output")) -> None:
    echo_json(get_client().get_wanted_cutoff(page=page, page_size=page_size), pretty=pretty)


@app.command("get_blocklist")
def get_blocklist(page: int = 1, page_size: int = 10, pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output")) -> None:
    echo_json(get_client().get_blocklist(page=page, page_size=page_size), pretty=pretty)


@app.command("get_blocklist_series")
def get_blocklist_series(page: int = 1, page_size: int = 10, pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output")) -> None:
    echo_json(get_client().get_blocklist_series(page=page, page_size=page_size), pretty=pretty)


@app.command("get_tags")
def get_tags(pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output")) -> None:
    echo_json(get_client().get_tags(), pretty=pretty)


@app.command("get_root_folders")
def get_root_folders(pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output")) -> None:
    echo_json(get_client().get_root_folders(), pretty=pretty)


@app.command("get_quality_profiles")
def get_quality_profiles(pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output")) -> None:
    echo_json(get_client().get_quality_profiles(), pretty=pretty)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
