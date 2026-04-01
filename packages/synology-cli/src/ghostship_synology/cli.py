from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

import typer

from .client import SynologyClient

app = typer.Typer(help="Synology File Station CLI interface.", no_args_is_help=True)


def echo_json(data: Any, pretty: bool = False) -> None:
    typer.echo(json.dumps(data, indent=2 if pretty else None))


def _parse_json_option(value: str | None, option_name: str) -> Any:
    if value is None:
        return None
    try:
        return json.loads(value)
    except json.JSONDecodeError as exc:
        raise typer.BadParameter(f"{option_name} must be valid JSON: {exc}") from exc


def get_client() -> SynologyClient:
    base_url = os.getenv("SYNOLOGY_URL")
    username = os.getenv("SYNOLOGY_USER")
    password = os.getenv("SYNOLOGY_PASS")
    verify_ssl = os.getenv("SYNOLOGY_VERIFY_SSL", "true").lower() == "true"
    if not base_url or not username or not password:
        print("Error: SYNOLOGY_URL, SYNOLOGY_USER, and SYNOLOGY_PASS environment variables must be set.", file=sys.stderr)
        raise typer.Exit(code=1)
    client = SynologyClient(base_url, username, password, verify_ssl)
    try:
        client.login()
    except Exception as exc:
        print(f"Login failed: {exc}", file=sys.stderr)
        raise typer.Exit(code=1)
    return client


def _run_logged_in(callback):
    client = get_client()
    try:
        return callback(client)
    finally:
        client.logout()


@app.command("call")
def call(api: str, method: str, version: int | None = typer.Option(None, "--version"), path: str | None = typer.Option(None, "--path"), param_json: str | None = typer.Option(None, "--param-json"), http_method: str | None = typer.Option(None, "--http-method"), pretty: bool = typer.Option(False, "--pretty")) -> None:
    echo_json(_run_logged_in(lambda client: client.call(api, method, version=version, path=path, params=_parse_json_option(param_json, "--param-json"), http_method=http_method)), pretty=pretty)


@app.command("get_info")
def get_info(query: str = typer.Option("all", "--query"), pretty: bool = typer.Option(False, "--pretty")) -> None:
    echo_json(_run_logged_in(lambda client: client.get_info(query=query)), pretty=pretty)


@app.command("login")
def login(pretty: bool = typer.Option(False, "--pretty")) -> None:
    client = get_client()
    try:
        echo_json({"sid": client.sid}, pretty=pretty)
    finally:
        client.logout()


@app.command("logout")
def logout(pretty: bool = typer.Option(False, "--pretty")) -> None:
    echo_json(_run_logged_in(lambda client: {"ok": client.logout()}), pretty=pretty)


@app.command("list_shares")
def list_shares(pretty: bool = typer.Option(False, "--pretty")) -> None:
    echo_json(_run_logged_in(lambda client: client.list_shares()), pretty=pretty)


@app.command("list_files")
def list_files(folder_path: str, offset: int = typer.Option(0, "--offset"), limit: int = typer.Option(100, "--limit"), sort_by: str = typer.Option("name", "--sort-by"), pretty: bool = typer.Option(False, "--pretty")) -> None:
    echo_json(_run_logged_in(lambda client: client.list_files(folder_path, offset=offset, limit=limit, sort_by=sort_by)), pretty=pretty)


@app.command("get_file_info")
def get_file_info(path: str, pretty: bool = typer.Option(False, "--pretty")) -> None:
    echo_json(_run_logged_in(lambda client: client.get_file_info(path)), pretty=pretty)


@app.command("search_start")
def search_start(folder_path: str, pattern: str, recursive: bool = typer.Option(True, "--recursive/--no-recursive"), pretty: bool = typer.Option(False, "--pretty")) -> None:
    echo_json(_run_logged_in(lambda client: {"taskid": client.search_start(folder_path, pattern, recursive=recursive)}), pretty=pretty)


@app.command("search_list")
def search_list(taskid: str, offset: int = typer.Option(0, "--offset"), limit: int = typer.Option(100, "--limit"), pretty: bool = typer.Option(False, "--pretty")) -> None:
    echo_json(_run_logged_in(lambda client: client.search_list(taskid, offset=offset, limit=limit)), pretty=pretty)


@app.command("create_folder")
def create_folder(folder_path: str, name: str, force_parent: bool = typer.Option(False, "--force-parent"), pretty: bool = typer.Option(False, "--pretty")) -> None:
    echo_json(_run_logged_in(lambda client: client.create_folder(folder_path, name, force_parent=force_parent)), pretty=pretty)


@app.command("rename")
def rename(path: str, name: str, pretty: bool = typer.Option(False, "--pretty")) -> None:
    echo_json(_run_logged_in(lambda client: client.rename(path, name)), pretty=pretty)


@app.command("delete")
def delete(path: str, recursive: bool = typer.Option(True, "--recursive/--no-recursive"), pretty: bool = typer.Option(False, "--pretty")) -> None:
    echo_json(_run_logged_in(lambda client: {"taskid": client.delete(path, recursive=recursive)}), pretty=pretty)


@app.command("download_file")
def download_file(path: str, mode: str = typer.Option("download", "--mode"), output: str = typer.Option(".", "--output"), pretty: bool = typer.Option(False, "--pretty")) -> None:
    def _download(client: SynologyClient):
        response = client.download_file(path, mode=mode)
        output_path = Path(output)
        destination = output_path / Path(path).name if output_path.is_dir() else output_path
        destination.write_bytes(response.content)
        return {"path": path, "output": str(destination)}
    echo_json(_run_logged_in(_download), pretty=pretty)


@app.command("upload_file")
def upload_file(folder_path: str, file_path: str, create_parents: bool = typer.Option(True, "--create-parents/--no-create-parents"), pretty: bool = typer.Option(False, "--pretty")) -> None:
    echo_json(_run_logged_in(lambda client: client.upload_file(folder_path, file_path, create_parents=create_parents)), pretty=pretty)


@app.command("copy")
def copy(path: str, destination: str, overwrite: bool = typer.Option(True, "--overwrite/--no-overwrite"), pretty: bool = typer.Option(False, "--pretty")) -> None:
    echo_json(_run_logged_in(lambda client: client.copy(path, destination, overwrite=overwrite)), pretty=pretty)


@app.command("move")
def move(path: str, destination: str, overwrite: bool = typer.Option(True, "--overwrite/--no-overwrite"), pretty: bool = typer.Option(False, "--pretty")) -> None:
    echo_json(_run_logged_in(lambda client: client.move(path, destination, overwrite=overwrite)), pretty=pretty)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
