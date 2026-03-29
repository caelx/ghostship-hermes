import typer
import os
import json
import sys
from typing import Optional, List, Any
from .client import PyLoadClient

app = typer.Typer(help="pyLoad-ng CLI interface.")


def echo_json(data: Any, pretty: bool = False):
    indent = 2 if pretty else None
    typer.echo(json.dumps(data, indent=indent))


def get_client() -> PyLoadClient:
    base_url = os.getenv("PYLOAD_URL")
    username = os.getenv("PYLOAD_USER")
    password = os.getenv("PYLOAD_PASS")

    if not base_url or not username or not password:
        print(
            "Error: PYLOAD_URL, PYLOAD_USER, and PYLOAD_PASS environment variables must be set.",
            file=sys.stderr,
        )
        raise typer.Exit(code=1)

    return PyLoadClient(base_url, username, password)


@app.command()
def status(
    pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output"),
):
    """Get server status information."""
    client = get_client()
    try:
        data = client.get_server_status()
        echo_json(data, pretty=pretty)
    except Exception as e:
        print(f"Error fetching status: {e}", file=sys.stderr)
        raise typer.Exit(code=1)


@app.command()
def downloads(
    pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output"),
):
    """Get currently running downloads."""
    client = get_client()
    try:
        data = client.get_downloads()
        echo_json(data, pretty=pretty)
    except Exception as e:
        print(f"Error fetching downloads: {e}", file=sys.stderr)
        raise typer.Exit(code=1)


@app.command()
def queue(
    pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output"),
):
    """List packages in the queue."""
    client = get_client()
    try:
        data = client.get_queue()
        echo_json(data, pretty=pretty)
    except Exception as e:
        print(f"Error fetching queue: {e}", file=sys.stderr)
        raise typer.Exit(code=1)


@app.command()
def add(
    name: str = typer.Argument(..., help="Package name"),
    links: List[str] = typer.Argument(..., help="List of URLs to add"),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output"),
):
    """Add a new package with links."""
    client = get_client()
    try:
        data = client.add_package(name, links)
        echo_json(data, pretty=pretty)
    except Exception as e:
        print(f"Error adding package: {e}", file=sys.stderr)
        raise typer.Exit(code=1)


@app.command()
def add_to_package(
    package_id: int = typer.Argument(..., help="Package ID"),
    links: List[str] = typer.Argument(..., help="List of URLs to add"),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output"),
):
    """Add links to an existing package."""
    client = get_client()
    try:
        data = client.add_files(package_id, links)
        echo_json(data, pretty=pretty)
    except Exception as e:
        print(f"Error adding files: {e}", file=sys.stderr)
        raise typer.Exit(code=1)


@app.command()
def delete(
    package_ids: List[int] = typer.Argument(..., help="List of package IDs to delete"),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output"),
):
    """Delete packages."""
    client = get_client()
    try:
        data = client.delete_packages(package_ids)
        echo_json(data, pretty=pretty)
    except Exception as e:
        print(f"Error deleting packages: {e}", file=sys.stderr)
        raise typer.Exit(code=1)


@app.command()
def pause(
    pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output"),
):
    """Toggle the pause state of the server."""
    client = get_client()
    try:
        data = client.toggle_pause()
        echo_json(data, pretty=pretty)
    except Exception as e:
        print(f"Error toggling pause: {e}", file=sys.stderr)
        raise typer.Exit(code=1)


@app.command()
def delete_finished(
    pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output"),
):
    """Delete finished downloads."""
    client = get_client()
    try:
        data = client.delete_finished()
        echo_json(data, pretty=pretty)
    except Exception as e:
        print(f"Error deleting finished: {e}", file=sys.stderr)
        raise typer.Exit(code=1)


@app.command()
def restart_failed(
    pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output"),
):
    """Restart failed downloads."""
    client = get_client()
    try:
        data = client.restart_failed()
        echo_json(data, pretty=pretty)
    except Exception as e:
        print(f"Error restarting failed: {e}", file=sys.stderr)
        raise typer.Exit(code=1)


@app.command()
def accounts(
    pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output"),
):
    """List configured download accounts."""
    client = get_client()
    try:
        data = client.get_accounts()
        echo_json(data, pretty=pretty)
    except Exception as e:
        print(f"Error fetching accounts: {e}", file=sys.stderr)
        raise typer.Exit(code=1)


@app.command()
def version(
    pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output"),
):
    """Get pyLoad server version."""
    client = get_client()
    try:
        data = client.get_server_version()
        echo_json(data, pretty=pretty)
    except Exception as e:
        print(f"Error fetching version: {e}", file=sys.stderr)
        raise typer.Exit(code=1)


@app.command()
def freespace(
    pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output"),
):
    """Get free disk space."""
    client = get_client()
    try:
        data = client.get_free_space()
        echo_json(data, pretty=pretty)
    except Exception as e:
        print(f"Error fetching free space: {e}", file=sys.stderr)
        raise typer.Exit(code=1)


def main():
    app()


if __name__ == "__main__":
    main()
