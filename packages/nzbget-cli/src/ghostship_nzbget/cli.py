from __future__ import annotations

import json
import os
import sys
from typing import Any

import typer

from .client import NZBGetClient

app = typer.Typer(help="NZBGet CLI interface.", no_args_is_help=True)


def echo_json(data: Any, pretty: bool = False):
    typer.echo(json.dumps(data, indent=2 if pretty else None))


def _parse_json_option(value: str | None, option_name: str) -> Any:
    if value is None:
        return None
    try:
        return json.loads(value)
    except json.JSONDecodeError as exc:
        raise typer.BadParameter(f"{option_name} must be valid JSON: {exc}") from exc


def get_client() -> NZBGetClient:
    base_url = os.getenv("NZBGET_URL")
    username = os.getenv("NZBGET_USER")
    password = os.getenv("NZBGET_PASS")
    if not base_url:
        print("Error: NZBGET_URL environment variable must be set.", file=sys.stderr)
        raise typer.Exit(code=1)
    return NZBGetClient(base_url, username, password)


@app.command("call")
def call(method: str, params_json: str | None = typer.Option(None, "--params-json"), pretty: bool = typer.Option(False, "--pretty")):
    echo_json(get_client().call(method, params=_parse_json_option(params_json, "--params-json")), pretty=pretty)


@app.command("get_version")
def get_version(pretty: bool = typer.Option(False, "--pretty")):
    echo_json({"version": get_client().get_version()}, pretty=pretty)


@app.command("shutdown")
def shutdown(pretty: bool = typer.Option(False, "--pretty")):
    echo_json({"ok": get_client().shutdown()}, pretty=pretty)


@app.command("reload")
def reload(pretty: bool = typer.Option(False, "--pretty")):
    echo_json({"ok": get_client().reload()}, pretty=pretty)


@app.command("get_status")
def get_status(pretty: bool = typer.Option(False, "--pretty")):
    echo_json(get_client().get_status(), pretty=pretty)


@app.command("list_groups")
def list_groups(pretty: bool = typer.Option(False, "--pretty")):
    echo_json(get_client().list_groups(), pretty=pretty)


@app.command("list_files")
def list_files(nzb_id: int, pretty: bool = typer.Option(False, "--pretty")):
    echo_json(get_client().list_files(nzb_id), pretty=pretty)


@app.command("get_history")
def get_history(pretty: bool = typer.Option(False, "--pretty")):
    echo_json(get_client().get_history(), pretty=pretty)


@app.command("append_url")
def append_url(url: str, category: str = typer.Option("", "--category"), priority: int = typer.Option(0, "--priority"), top: bool = typer.Option(False, "--top"), pretty: bool = typer.Option(False, "--pretty")):
    echo_json({"nzbid": get_client().append_url(url, category=category, priority=priority, top=top)}, pretty=pretty)


@app.command("edit_queue")
def edit_queue(command: str, offset: int, size: int, ids_json: str = typer.Option(..., "--ids-json"), pretty: bool = typer.Option(False, "--pretty")):
    echo_json({"ok": get_client().edit_queue(command, offset, size, _parse_json_option(ids_json, "--ids-json"))}, pretty=pretty)


@app.command("disk_scan")
def disk_scan(pretty: bool = typer.Option(False, "--pretty")):
    echo_json({"ok": get_client().disk_scan()}, pretty=pretty)


@app.command("get_log")
def get_log(id_from: int, count: int, pretty: bool = typer.Option(False, "--pretty")):
    echo_json(get_client().get_log(id_from, count), pretty=pretty)


@app.command("set_rate")
def set_rate(limit_kb: int, pretty: bool = typer.Option(False, "--pretty")):
    echo_json({"ok": get_client().set_rate(limit_kb)}, pretty=pretty)


@app.command("pause_download")
def pause_download(pretty: bool = typer.Option(False, "--pretty")):
    echo_json({"ok": get_client().pause_download()}, pretty=pretty)


@app.command("resume_download")
def resume_download(pretty: bool = typer.Option(False, "--pretty")):
    echo_json({"ok": get_client().resume_download()}, pretty=pretty)


@app.command("pause_post")
def pause_post(pretty: bool = typer.Option(False, "--pretty")):
    echo_json({"ok": get_client().pause_post()}, pretty=pretty)


@app.command("resume_post")
def resume_post(pretty: bool = typer.Option(False, "--pretty")):
    echo_json({"ok": get_client().resume_post()}, pretty=pretty)


@app.command("pause_scan")
def pause_scan(pretty: bool = typer.Option(False, "--pretty")):
    echo_json({"ok": get_client().pause_scan()}, pretty=pretty)


@app.command("resume_scan")
def resume_scan(pretty: bool = typer.Option(False, "--pretty")):
    echo_json({"ok": get_client().resume_scan()}, pretty=pretty)


@app.command("get_config")
def get_config(pretty: bool = typer.Option(False, "--pretty")):
    echo_json(get_client().get_config(), pretty=pretty)


@app.command("save_config")
def save_config(config_json: str = typer.Option(..., "--config-json"), pretty: bool = typer.Option(False, "--pretty")):
    echo_json({"ok": get_client().save_config(_parse_json_option(config_json, "--config-json"))}, pretty=pretty)


def main():
    app()


if __name__ == "__main__":
    main()
