from __future__ import annotations

import json
import os
import sys
from typing import Any

import typer

from .client import RommClient

HELP_TEXT = """RomM CLI interface.

Auth:
- Set ROMM_URL.
- Preferred: set ROMM_USERNAME and ROMM_PASSWORD.
- Optional override: set ROMM_TOKEN.
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


def get_client() -> RommClient:
    base_url = os.getenv("ROMM_URL")
    token = os.getenv("ROMM_TOKEN")
    username = os.getenv("ROMM_USERNAME")
    password = os.getenv("ROMM_PASSWORD")
    if not base_url:
        print("Error: ROMM_URL must be set.", file=sys.stderr)
        raise typer.Exit(code=1)
    if not token and not (username and password):
        print("Error: set ROMM_TOKEN or ROMM_USERNAME and ROMM_PASSWORD.", file=sys.stderr)
        raise typer.Exit(code=1)
    return RommClient(base_url, token=token, username=username, password=password)


@app.command("request")
def request(method: str, path: str, param: list[str] = typer.Option([], "--param"), body_json: str | None = typer.Option(None, "--body-json"), pretty: bool = typer.Option(False, "--pretty")) -> None:
    echo_json(get_client().request(method, path, params=_parse_params(param) or None, json_data=_parse_json_option(body_json, "--body-json")), pretty=pretty)


@app.command("get_heartbeat")
def get_heartbeat(pretty: bool = typer.Option(False, "--pretty")) -> None:
    echo_json(get_client().get_heartbeat(), pretty=pretty)


@app.command("get_platforms")
def get_platforms(pretty: bool = typer.Option(False, "--pretty")) -> None:
    echo_json(get_client().get_platforms(), pretty=pretty)


@app.command("get_libraries")
def get_libraries(pretty: bool = typer.Option(False, "--pretty")) -> None:
    echo_json(get_client().get_libraries(), pretty=pretty)


@app.command("get_roms")
def get_roms(page: int = typer.Option(1, "--page"), page_size: int = typer.Option(24, "--page-size"), platform: str | None = typer.Option(None, "--platform"), pretty: bool = typer.Option(False, "--pretty")) -> None:
    echo_json(get_client().get_roms(page=page, page_size=page_size, platform=platform), pretty=pretty)


@app.command("get_rom")
def get_rom(rom_id: int, pretty: bool = typer.Option(False, "--pretty")) -> None:
    echo_json(get_client().get_rom(rom_id), pretty=pretty)


@app.command("update_rom")
def update_rom(rom_id: int, body_json: str = typer.Option(..., "--body-json"), pretty: bool = typer.Option(False, "--pretty")) -> None:
    echo_json(get_client().update_rom(rom_id, _parse_json_option(body_json, "--body-json")), pretty=pretty)


@app.command("delete_rom")
def delete_rom(rom_id: int, pretty: bool = typer.Option(False, "--pretty")) -> None:
    echo_json(get_client().delete_rom(rom_id), pretty=pretty)


@app.command("get_scans")
def get_scans(pretty: bool = typer.Option(False, "--pretty")) -> None:
    echo_json(get_client().get_scans(), pretty=pretty)


@app.command("start_scan")
def start_scan(library_id: int | None = typer.Option(None, "--library-id"), pretty: bool = typer.Option(False, "--pretty")) -> None:
    echo_json(get_client().start_scan(library_id), pretty=pretty)


@app.command("get_collections")
def get_collections(pretty: bool = typer.Option(False, "--pretty")) -> None:
    echo_json(get_client().get_collections(), pretty=pretty)


@app.command("get_config")
def get_config(pretty: bool = typer.Option(False, "--pretty")) -> None:
    echo_json(get_client().get_config(), pretty=pretty)


@app.command("get_saves")
def get_saves(page: int = typer.Option(1, "--page"), page_size: int = typer.Option(24, "--page-size"), pretty: bool = typer.Option(False, "--pretty")) -> None:
    echo_json(get_client().get_saves(page=page, page_size=page_size), pretty=pretty)


@app.command("get_saves_summary")
def get_saves_summary(pretty: bool = typer.Option(False, "--pretty")) -> None:
    echo_json(get_client().get_saves_summary(), pretty=pretty)


@app.command("get_save")
def get_save(save_id: int, pretty: bool = typer.Option(False, "--pretty")) -> None:
    echo_json(get_client().get_save(save_id), pretty=pretty)


@app.command("get_users")
def get_users(pretty: bool = typer.Option(False, "--pretty")) -> None:
    echo_json(get_client().get_users(), pretty=pretty)


@app.command("get_user_me")
def get_user_me(pretty: bool = typer.Option(False, "--pretty")) -> None:
    echo_json(get_client().get_user_me(), pretty=pretty)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
