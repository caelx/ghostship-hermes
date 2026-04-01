from __future__ import annotations

import json
import os
import sys
from typing import Any

import typer

from .client import TautulliClient

app = typer.Typer(help="Tautulli CLI interface.", no_args_is_help=True)


def echo_json(data: Any, pretty: bool = False) -> None:
    typer.echo(json.dumps(data, indent=2 if pretty else None))


def _parse_params(values: list[str]) -> dict[str, str]:
    params: dict[str, str] = {}
    for value in values:
        if "=" not in value:
            raise typer.BadParameter(f"parameter must use key=value form: {value}")
        key, raw = value.split("=", 1)
        params[key] = raw
    return params


def get_client() -> TautulliClient:
    base_url = os.getenv("TAUTULLI_URL")
    api_key = os.getenv("TAUTULLI_API_KEY")
    if not base_url or not api_key:
        print("Error: TAUTULLI_URL and TAUTULLI_API_KEY environment variables must be set.", file=sys.stderr)
        raise typer.Exit(code=1)
    return TautulliClient(base_url, api_key)


@app.command("call")
def call(cmd: str, param: list[str] = typer.Option([], "--param"), pretty: bool = typer.Option(False, "--pretty")) -> None:
    echo_json(get_client().call(cmd, **_parse_params(param)), pretty=pretty)


@app.command("get_server_status")
def get_server_status(pretty: bool = typer.Option(False, "--pretty")) -> None:
    echo_json(get_client().get_server_status(), pretty=pretty)


@app.command("get_tautulli_info")
def get_tautulli_info(pretty: bool = typer.Option(False, "--pretty")) -> None:
    echo_json(get_client().get_tautulli_info(), pretty=pretty)


@app.command("get_status")
def get_status(pretty: bool = typer.Option(False, "--pretty")) -> None:
    echo_json(get_client().get_status(), pretty=pretty)


@app.command("get_activity")
def get_activity(pretty: bool = typer.Option(False, "--pretty")) -> None:
    echo_json(get_client().get_activity(), pretty=pretty)


@app.command("terminate_session")
def terminate_session(session_id: str, message: str | None = typer.Option(None, "--message"), pretty: bool = typer.Option(False, "--pretty")) -> None:
    echo_json(get_client().terminate_session(session_id, message=message), pretty=pretty)


@app.command("get_history")
def get_history(page: int = typer.Option(1, "--page"), length: int = typer.Option(10, "--length"), search: str | None = typer.Option(None, "--search"), order_column: str = typer.Option("date", "--order-column"), order_dir: str = typer.Option("desc", "--order-dir"), pretty: bool = typer.Option(False, "--pretty")) -> None:
    echo_json(get_client().get_history(page=page, length=length, search=search, order_column=order_column, order_dir=order_dir), pretty=pretty)


@app.command("get_libraries")
def get_libraries(pretty: bool = typer.Option(False, "--pretty")) -> None:
    echo_json(get_client().get_libraries(), pretty=pretty)


@app.command("get_library_user_stats")
def get_library_user_stats(section_id: int, pretty: bool = typer.Option(False, "--pretty")) -> None:
    echo_json(get_client().get_library_user_stats(section_id), pretty=pretty)


@app.command("get_users")
def get_users(pretty: bool = typer.Option(False, "--pretty")) -> None:
    echo_json(get_client().get_users(), pretty=pretty)


@app.command("get_user_player_stats")
def get_user_player_stats(user_id: int, pretty: bool = typer.Option(False, "--pretty")) -> None:
    echo_json(get_client().get_user_player_stats(user_id), pretty=pretty)


@app.command("get_user_watch_time_stats")
def get_user_watch_time_stats(user_id: int, pretty: bool = typer.Option(False, "--pretty")) -> None:
    echo_json(get_client().get_user_watch_time_stats(user_id), pretty=pretty)


@app.command("get_metadata")
def get_metadata(rating_key: int, pretty: bool = typer.Option(False, "--pretty")) -> None:
    echo_json(get_client().get_metadata(rating_key), pretty=pretty)


@app.command("search")
def search(query: str, limit: int = typer.Option(10, "--limit"), pretty: bool = typer.Option(False, "--pretty")) -> None:
    echo_json(get_client().search(query, limit=limit), pretty=pretty)


@app.command("restart")
def restart(pretty: bool = typer.Option(False, "--pretty")) -> None:
    echo_json(get_client().restart(), pretty=pretty)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
