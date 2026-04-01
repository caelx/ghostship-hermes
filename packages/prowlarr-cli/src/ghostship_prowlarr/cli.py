from __future__ import annotations

import json
import os
import sys
from typing import Any

import typer

from .client import ProwlarrClient

app = typer.Typer(help="Prowlarr CLI interface.", no_args_is_help=True)


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


def get_client() -> ProwlarrClient:
    base_url = os.getenv("PROWLARR_URL")
    api_key = os.getenv("PROWLARR_API_KEY")
    if not base_url or not api_key:
        print(
            "Error: PROWLARR_URL and PROWLARR_API_KEY environment variables must be set.",
            file=sys.stderr,
        )
        raise typer.Exit(code=1)
    return ProwlarrClient(base_url, api_key)


@app.command("request")
def request(method: str, path: str, param: list[str] = typer.Option([], "--param", help="Repeat key=value query parameters."), body_json: str | None = typer.Option(None, "--body-json", help="Optional JSON request body."), pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output")) -> None:
    echo_json(get_client().request(method, path, params=_parse_params(param) or None, json_data=_parse_json_option(body_json, "--body-json")), pretty=pretty)


@app.command("get_status")
def get_status(pretty: bool = typer.Option(False, "--pretty")) -> None:
    echo_json(get_client().get_status(), pretty=pretty)


@app.command("get_indexers")
def get_indexers(indexer_id: int | None = None, pretty: bool = typer.Option(False, "--pretty")) -> None:
    echo_json(get_client().get_indexers(indexer_id), pretty=pretty)


@app.command("search")
def search(query: str, category_json: str | None = typer.Option(None, "--category-json", help="Optional JSON array of category ids"), pretty: bool = typer.Option(False, "--pretty")) -> None:
    categories = _parse_json_option(category_json, "--category-json") if category_json else None
    echo_json(get_client().search(query, categories=categories), pretty=pretty)


@app.command("get_applications")
def get_applications(app_id: int | None = None, pretty: bool = typer.Option(False, "--pretty")) -> None:
    echo_json(get_client().get_applications(app_id), pretty=pretty)


@app.command("get_history")
def get_history(page: int = 1, page_size: int = 10, pretty: bool = typer.Option(False, "--pretty")) -> None:
    echo_json(get_client().get_history(page=page, page_size=page_size), pretty=pretty)


@app.command("get_indexer_stats")
def get_indexer_stats(pretty: bool = typer.Option(False, "--pretty")) -> None:
    echo_json(get_client().get_indexer_stats(), pretty=pretty)


@app.command("get_indexer_status")
def get_indexer_status(pretty: bool = typer.Option(False, "--pretty")) -> None:
    echo_json(get_client().get_indexer_status(), pretty=pretty)


@app.command("run_command")
def run_command(name: str, args: str | None = typer.Option(None, "--args", help="JSON object merged into the command payload"), pretty: bool = typer.Option(False, "--pretty")) -> None:
    kwargs = _parse_json_option(args, "--args") or {}
    echo_json(get_client().run_command(name, **kwargs), pretty=pretty)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
