from __future__ import annotations

import json
import os
import sys
from typing import Any

import typer

from .client import PyLoadClient

app = typer.Typer(help="pyLoad-ng CLI interface.", no_args_is_help=True)


def echo_json(data: Any, pretty: bool = False):
    typer.echo(json.dumps(data, indent=2 if pretty else None))


def _parse_json_option(value: str | None, option_name: str) -> Any:
    if value is None:
        return None
    try:
        return json.loads(value)
    except json.JSONDecodeError as exc:
        raise typer.BadParameter(f"{option_name} must be valid JSON: {exc}") from exc


def get_client() -> PyLoadClient:
    base_url = os.getenv("PYLOAD_URL")
    username = os.getenv("PYLOAD_USER")
    password = os.getenv("PYLOAD_PASS")
    if not base_url:
        print("Error: PYLOAD_URL environment variable must be set.", file=sys.stderr)
        raise typer.Exit(code=1)
    return PyLoadClient(base_url, username, password)


@app.command("request")
def request(method: str, path: str, param_json: str | None = typer.Option(None, "--param-json"), body_json: str | None = typer.Option(None, "--body-json"), pretty: bool = typer.Option(False, "--pretty")):
    echo_json(get_client().request(method, path, params=_parse_json_option(param_json, "--param-json"), json_data=_parse_json_option(body_json, "--body-json")), pretty=pretty)


@app.command("get_server_status")
def get_server_status(pretty: bool = typer.Option(False, "--pretty")):
    echo_json(get_client().get_server_status(), pretty=pretty)


@app.command("get_downloads")
def get_downloads(pretty: bool = typer.Option(False, "--pretty")):
    echo_json(get_client().get_downloads(), pretty=pretty)


@app.command("get_queue")
def get_queue(pretty: bool = typer.Option(False, "--pretty")):
    echo_json(get_client().get_queue(), pretty=pretty)


@app.command("add_package")
def add_package(name: str, links_json: str = typer.Option(..., "--links-json"), pretty: bool = typer.Option(False, "--pretty")):
    echo_json(get_client().add_package(name, _parse_json_option(links_json, "--links-json")), pretty=pretty)


@app.command("add_files")
def add_files(package_id: int, links_json: str = typer.Option(..., "--links-json"), pretty: bool = typer.Option(False, "--pretty")):
    echo_json(get_client().add_files(package_id, _parse_json_option(links_json, "--links-json")), pretty=pretty)


@app.command("delete_packages")
def delete_packages(package_ids_json: str = typer.Option(..., "--package-ids-json"), pretty: bool = typer.Option(False, "--pretty")):
    echo_json(get_client().delete_packages(_parse_json_option(package_ids_json, "--package-ids-json")), pretty=pretty)


@app.command("toggle_pause")
def toggle_pause(pretty: bool = typer.Option(False, "--pretty")):
    echo_json(get_client().toggle_pause(), pretty=pretty)


@app.command("get_config")
def get_config(pretty: bool = typer.Option(False, "--pretty")):
    echo_json(get_client().get_config(), pretty=pretty)


@app.command("delete_finished")
def delete_finished(pretty: bool = typer.Option(False, "--pretty")):
    echo_json(get_client().delete_finished(), pretty=pretty)


@app.command("restart_failed")
def restart_failed(pretty: bool = typer.Option(False, "--pretty")):
    echo_json(get_client().restart_failed(), pretty=pretty)


@app.command("stop_all_downloads")
def stop_all_downloads(pretty: bool = typer.Option(False, "--pretty")):
    echo_json(get_client().stop_all_downloads(), pretty=pretty)


@app.command("get_accounts")
def get_accounts(refresh: bool = typer.Option(False, "--refresh"), pretty: bool = typer.Option(False, "--pretty")):
    echo_json(get_client().get_accounts(refresh=refresh), pretty=pretty)


@app.command("add_account")
def add_account(plugin: str, login: str, password: str, pretty: bool = typer.Option(False, "--pretty")):
    echo_json(get_client().add_account(plugin, login, password), pretty=pretty)


@app.command("remove_account")
def remove_account(plugin: str, login: str, pretty: bool = typer.Option(False, "--pretty")):
    echo_json(get_client().remove_account(plugin, login), pretty=pretty)


@app.command("get_server_version")
def get_server_version(pretty: bool = typer.Option(False, "--pretty")):
    echo_json(get_client().get_server_version(), pretty=pretty)


@app.command("get_free_space")
def get_free_space(pretty: bool = typer.Option(False, "--pretty")):
    echo_json(get_client().get_free_space(), pretty=pretty)


def main():
    app()


if __name__ == "__main__":
    main()
