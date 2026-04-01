from __future__ import annotations

import json
import os
import sys
from typing import Any

import typer

from .client import PlexClient

app = typer.Typer(help="Plex Media Server CLI interface.", no_args_is_help=True)


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


def get_client() -> PlexClient:
    base_url = os.getenv("PLEX_URL")
    token = os.getenv("PLEX_TOKEN")
    if not base_url or not token:
        print("Error: PLEX_URL and PLEX_TOKEN environment variables must be set.", file=sys.stderr)
        raise typer.Exit(code=1)
    return PlexClient(base_url, token)


@app.command("request")
def request(method: str, path: str, param: list[str] = typer.Option([], "--param"), body_json: str | None = typer.Option(None, "--body-json"), pretty: bool = typer.Option(False, "--pretty")) -> None:
    echo_json(get_client().request(method, path, params=_parse_params(param) or None, json_data=_parse_json_option(body_json, "--body-json")), pretty=pretty)


@app.command("get_identity")
def get_identity(pretty: bool = typer.Option(False, "--pretty")) -> None:
    echo_json(get_client().get_identity(), pretty=pretty)


@app.command("get_server_info")
def get_server_info(pretty: bool = typer.Option(False, "--pretty")) -> None:
    echo_json(get_client().get_server_info(), pretty=pretty)


@app.command("get_status_sessions")
def get_status_sessions(pretty: bool = typer.Option(False, "--pretty")) -> None:
    echo_json(get_client().get_status_sessions(), pretty=pretty)


@app.command("get_activities")
def get_activities(pretty: bool = typer.Option(False, "--pretty")) -> None:
    echo_json(get_client().get_activities(), pretty=pretty)


@app.command("get_library_sections")
def get_library_sections(pretty: bool = typer.Option(False, "--pretty")) -> None:
    echo_json(get_client().get_library_sections(), pretty=pretty)


@app.command("get_library_section")
def get_library_section(section_id: int, pretty: bool = typer.Option(False, "--pretty")) -> None:
    echo_json(get_client().get_library_section(section_id), pretty=pretty)


@app.command("get_library_filters")
def get_library_filters(section_id: int, pretty: bool = typer.Option(False, "--pretty")) -> None:
    echo_json(get_client().get_library_filters(section_id), pretty=pretty)


@app.command("get_library_sorts")
def get_library_sorts(section_id: int, pretty: bool = typer.Option(False, "--pretty")) -> None:
    echo_json(get_client().get_library_sorts(section_id), pretty=pretty)


@app.command("refresh_library")
def refresh_library(section_id: int | None = typer.Option(None, "--section-id"), pretty: bool = typer.Option(False, "--pretty")) -> None:
    echo_json(get_client().refresh_library(section_id), pretty=pretty)


@app.command("get_metadata")
def get_metadata(rating_key: int, pretty: bool = typer.Option(False, "--pretty")) -> None:
    echo_json(get_client().get_metadata(rating_key), pretty=pretty)


@app.command("get_metadata_children")
def get_metadata_children(rating_key: int, pretty: bool = typer.Option(False, "--pretty")) -> None:
    echo_json(get_client().get_metadata_children(rating_key), pretty=pretty)


@app.command("get_playlists")
def get_playlists(pretty: bool = typer.Option(False, "--pretty")) -> None:
    echo_json(get_client().get_playlists(), pretty=pretty)


@app.command("get_playlist_items")
def get_playlist_items(playlist_id: int, pretty: bool = typer.Option(False, "--pretty")) -> None:
    echo_json(get_client().get_playlist_items(playlist_id), pretty=pretty)


@app.command("get_collections")
def get_collections(section_id: int, pretty: bool = typer.Option(False, "--pretty")) -> None:
    echo_json(get_client().get_collections(section_id), pretty=pretty)


@app.command("get_preferences")
def get_preferences(pretty: bool = typer.Option(False, "--pretty")) -> None:
    echo_json(get_client().get_preferences(), pretty=pretty)


@app.command("get_butler_tasks")
def get_butler_tasks(pretty: bool = typer.Option(False, "--pretty")) -> None:
    echo_json(get_client().get_butler_tasks(), pretty=pretty)


@app.command("get_statistics")
def get_statistics(pretty: bool = typer.Option(False, "--pretty")) -> None:
    echo_json(get_client().get_statistics(), pretty=pretty)


@app.command("terminate_session")
def terminate_session(session_id: int, pretty: bool = typer.Option(False, "--pretty")) -> None:
    echo_json(get_client().terminate_session(session_id), pretty=pretty)


@app.command("get_session")
def get_session(session_id: int, pretty: bool = typer.Option(False, "--pretty")) -> None:
    echo_json(get_client().get_session(session_id), pretty=pretty)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
