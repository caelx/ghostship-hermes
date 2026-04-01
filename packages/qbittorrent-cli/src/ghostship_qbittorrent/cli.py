from __future__ import annotations

import json
import os
import sys
from typing import Any

import typer

from .client import QBitClient

app = typer.Typer(help="qBittorrent CLI interface.", no_args_is_help=True)


def echo_json(data: Any, pretty: bool = False):
    typer.echo(json.dumps(data, indent=2 if pretty else None))


def _parse_json_option(value: str | None, option_name: str) -> Any:
    if value is None:
        return None
    try:
        return json.loads(value)
    except json.JSONDecodeError as exc:
        raise typer.BadParameter(f"{option_name} must be valid JSON: {exc}") from exc


def _parse_pairs(values: list[str]) -> dict[str, str]:
    params: dict[str, str] = {}
    for value in values:
        if "=" not in value:
            raise typer.BadParameter(f"parameter must use key=value form: {value}")
        key, raw = value.split("=", 1)
        params[key] = raw
    return params


def get_client() -> QBitClient:
    base_url = os.getenv("QBITTORRENT_URL")
    username = os.getenv("QBITTORRENT_USER")
    password = os.getenv("QBITTORRENT_PASS")
    if not base_url:
        print("Error: QBITTORRENT_URL environment variable must be set.", file=sys.stderr)
        raise typer.Exit(code=1)
    return QBitClient(base_url, username, password)


@app.command("request")
def request(method: str, path: str, param: list[str] = typer.Option([], "--param"), data: list[str] = typer.Option([], "--data"), body_json: str | None = typer.Option(None, "--body-json"), pretty: bool = typer.Option(False, "--pretty")):
    echo_json(get_client().request(method, path, params=_parse_pairs(param) or None, data=_parse_pairs(data) or None, json_data=_parse_json_option(body_json, "--body-json")), pretty=pretty)


@app.command("login")
def login(pretty: bool = typer.Option(False, "--pretty")):
    echo_json({"ok": get_client().login()}, pretty=pretty)


@app.command("logout")
def logout(pretty: bool = typer.Option(False, "--pretty")):
    echo_json({"ok": get_client().logout()}, pretty=pretty)


@app.command("get_app_version")
def get_app_version(pretty: bool = typer.Option(False, "--pretty")):
    echo_json({"version": get_client().get_app_version()}, pretty=pretty)


@app.command("get_api_version")
def get_api_version(pretty: bool = typer.Option(False, "--pretty")):
    echo_json({"version": get_client().get_api_version()}, pretty=pretty)


@app.command("shutdown")
def shutdown(pretty: bool = typer.Option(False, "--pretty")):
    echo_json({"ok": get_client().shutdown()}, pretty=pretty)


@app.command("get_preferences")
def get_preferences(pretty: bool = typer.Option(False, "--pretty")):
    echo_json(get_client().get_preferences(), pretty=pretty)


@app.command("set_preferences")
def set_preferences(body_json: str = typer.Option(..., "--body-json"), pretty: bool = typer.Option(False, "--pretty")):
    echo_json({"ok": get_client().set_preferences(_parse_json_option(body_json, "--body-json"))}, pretty=pretty)


@app.command("get_log")
def get_log(last_known_id: int = typer.Option(-1, "--last-known-id"), pretty: bool = typer.Option(False, "--pretty")):
    echo_json(get_client().get_log(last_known_id=last_known_id), pretty=pretty)


@app.command("get_main_data")
def get_main_data(rid: int = typer.Option(0, "--rid"), pretty: bool = typer.Option(False, "--pretty")):
    echo_json(get_client().get_main_data(rid=rid), pretty=pretty)


@app.command("get_transfer_info")
def get_transfer_info(pretty: bool = typer.Option(False, "--pretty")):
    echo_json(get_client().get_transfer_info(), pretty=pretty)


@app.command("get_speed_limits_mode")
def get_speed_limits_mode(pretty: bool = typer.Option(False, "--pretty")):
    echo_json({"mode": get_client().get_speed_limits_mode()}, pretty=pretty)


@app.command("toggle_speed_limits_mode")
def toggle_speed_limits_mode(pretty: bool = typer.Option(False, "--pretty")):
    echo_json({"ok": get_client().toggle_speed_limits_mode()}, pretty=pretty)


@app.command("get_torrents")
def get_torrents(filter_type: str | None = typer.Option(None, "--filter-type"), category: str | None = typer.Option(None, "--category"), sort: str | None = typer.Option(None, "--sort"), reverse: bool = typer.Option(False, "--reverse"), pretty: bool = typer.Option(False, "--pretty")):
    echo_json(get_client().get_torrents(filter_type=filter_type, category=category, sort=sort, reverse=reverse), pretty=pretty)


@app.command("add_torrent")
def add_torrent(url: list[str], save_path: str | None = typer.Option(None, "--save-path"), category: str | None = typer.Option(None, "--category"), pretty: bool = typer.Option(False, "--pretty")):
    echo_json({"ok": get_client().add_torrent(url, save_path=save_path, category=category)}, pretty=pretty)


@app.command("delete_torrents")
def delete_torrents(hashes: list[str], delete_files: bool = typer.Option(False, "--delete-files"), pretty: bool = typer.Option(False, "--pretty")):
    echo_json({"ok": get_client().delete_torrents(hashes, delete_files=delete_files)}, pretty=pretty)


@app.command("pause_torrents")
def pause_torrents(hashes: list[str], pretty: bool = typer.Option(False, "--pretty")):
    echo_json({"ok": get_client().pause_torrents(hashes)}, pretty=pretty)


@app.command("resume_torrents")
def resume_torrents(hashes: list[str], pretty: bool = typer.Option(False, "--pretty")):
    echo_json({"ok": get_client().resume_torrents(hashes)}, pretty=pretty)


@app.command("search_start")
def search_start(pattern: str, category: str = typer.Option("all", "--category"), plugins: str = typer.Option("all", "--plugins"), pretty: bool = typer.Option(False, "--pretty")):
    echo_json(get_client().search_start(pattern, category=category, plugins=plugins), pretty=pretty)


@app.command("search_status")
def search_status(search_id: int | None = typer.Option(None, "--search-id"), pretty: bool = typer.Option(False, "--pretty")):
    echo_json(get_client().search_status(search_id), pretty=pretty)


@app.command("search_results")
def search_results(search_id: int, limit: int = typer.Option(10, "--limit"), offset: int = typer.Option(0, "--offset"), pretty: bool = typer.Option(False, "--pretty")):
    echo_json(get_client().search_results(search_id, limit=limit, offset=offset), pretty=pretty)


@app.command("get_rss_data")
def get_rss_data(with_data: bool = typer.Option(True, "--with-data/--no-with-data"), pretty: bool = typer.Option(False, "--pretty")):
    echo_json(get_client().get_rss_data(with_data=with_data), pretty=pretty)


def main():
    app()


if __name__ == "__main__":
    main()
