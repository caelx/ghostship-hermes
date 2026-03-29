import json
import os
import sys
from typing import Any, Optional

import typer

from .client import RommClient

HELP_TEXT = """Romm (ROM Manager) CLI interface.

Auth:
- Set ROMM_URL to the RomM base URL.
- Preferred: set ROMM_USERNAME and ROMM_PASSWORD. The CLI exchanges them at /api/token.
- Optional override: set ROMM_TOKEN if you already have a bearer token.
"""

app = typer.Typer(help=HELP_TEXT, no_args_is_help=True)


def echo_json(data: Any, pretty: bool = False):
    indent = 2 if pretty else None
    typer.echo(json.dumps(data, indent=indent))


def get_client() -> RommClient:
    base_url = os.getenv("ROMM_URL")
    token = os.getenv("ROMM_TOKEN")
    username = os.getenv("ROMM_USERNAME")
    password = os.getenv("ROMM_PASSWORD")

    if not base_url:
        print(
            "Error: ROMM_URL must be set.",
            file=sys.stderr,
        )
        raise typer.Exit(code=1)

    if not token and not (username and password):
        print(
            "Error: set ROMM_TOKEN or ROMM_USERNAME and ROMM_PASSWORD.",
            file=sys.stderr,
        )
        raise typer.Exit(code=1)

    return RommClient(base_url, token=token, username=username, password=password)


@app.command()
def heartbeat(pretty: bool = typer.Option(False, "--pretty")):
    """Check Romm API heartbeat."""
    client = get_client()
    try:
        data = client.get_heartbeat()
        echo_json(data, pretty=pretty)
    except Exception as e:
        echo_json({"error": str(e)}, pretty=pretty)
        raise typer.Exit(code=1)


@app.command()
def list_roms(
    page: int = 1,
    page_size: int = 24,
    platform: Optional[str] = None,
    pretty: bool = typer.Option(False, "--pretty"),
):
    """List ROMs in the library."""
    client = get_client()
    try:
        data = client.get_roms(page=page, page_size=page_size, platform=platform)
        echo_json(data, pretty=pretty)
    except Exception as e:
        echo_json({"error": str(e)}, pretty=pretty)
        raise typer.Exit(code=1)


@app.command()
def get_rom(rom_id: int, pretty: bool = typer.Option(False, "--pretty")):
    """Get detailed information for a ROM."""
    client = get_client()
    try:
        data = client.get_rom(rom_id)
        echo_json(data, pretty=pretty)
    except Exception as e:
        echo_json({"error": str(e)}, pretty=pretty)
        raise typer.Exit(code=1)


@app.command()
def platforms(pretty: bool = typer.Option(False, "--pretty")):
    """List all available platforms."""
    client = get_client()
    try:
        data = client.get_platforms()
        echo_json(data, pretty=pretty)
    except Exception as e:
        echo_json({"error": str(e)}, pretty=pretty)
        raise typer.Exit(code=1)


@app.command()
def scan(
    library_id: Optional[int] = typer.Option(None, "--id", help="Library ID to scan"),
    pretty: bool = typer.Option(False, "--pretty"),
):
    """Start a library scan."""
    client = get_client()
    try:
        data = client.start_scan(library_id)
        echo_json(data, pretty=pretty)
    except Exception as e:
        echo_json({"error": str(e)}, pretty=pretty)
        raise typer.Exit(code=1)


@app.command()
def list_collections(pretty: bool = typer.Option(False, "--pretty")):
    """List all collections."""
    client = get_client()
    try:
        data = client.get_collections()
        echo_json(data, pretty=pretty)
    except Exception as e:
        echo_json({"error": str(e)}, pretty=pretty)
        raise typer.Exit(code=1)


@app.command()
def config(pretty: bool = typer.Option(False, "--pretty")):
    """Get Romm configuration."""
    client = get_client()
    try:
        data = client.get_config()
        echo_json(data, pretty=pretty)
    except Exception as e:
        echo_json({"error": str(e)}, pretty=pretty)
        raise typer.Exit(code=1)


@app.command()
def saves(
    page: int = 1, page_size: int = 24, pretty: bool = typer.Option(False, "--pretty")
):
    """List save files."""
    client = get_client()
    try:
        data = client.get_saves(page=page, page_size=page_size)
        echo_json(data, pretty=pretty)
    except Exception as e:
        echo_json({"error": str(e)}, pretty=pretty)
        raise typer.Exit(code=1)


@app.command()
def saves_summary(pretty: bool = typer.Option(False, "--pretty")):
    """Get save files summary."""
    client = get_client()
    try:
        data = client.get_saves_summary()
        echo_json(data, pretty=pretty)
    except Exception as e:
        echo_json({"error": str(e)}, pretty=pretty)
        raise typer.Exit(code=1)


@app.command()
def users(pretty: bool = typer.Option(False, "--pretty")):
    """List users."""
    client = get_client()
    try:
        data = client.get_users()
        echo_json(data, pretty=pretty)
    except Exception as e:
        echo_json({"error": str(e)}, pretty=pretty)
        raise typer.Exit(code=1)


@app.command()
def me(pretty: bool = typer.Option(False, "--pretty")):
    """Get current user info."""
    client = get_client()
    try:
        data = client.get_user_me()
        echo_json(data, pretty=pretty)
    except Exception as e:
        echo_json({"error": str(e)}, pretty=pretty)
        raise typer.Exit(code=1)


def main():
    app()


if __name__ == "__main__":
    main()
