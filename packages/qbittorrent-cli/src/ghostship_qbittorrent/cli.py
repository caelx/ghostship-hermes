import typer
import os
import json
import sys
from typing import Optional, List, Any
from .client import QBitClient

app = typer.Typer(help="qBittorrent CLI interface.")


def echo_json(data: Any, pretty: bool = False):
    indent = 2 if pretty else None
    typer.echo(json.dumps(data, indent=indent))


def get_client() -> QBitClient:
    base_url = os.getenv("QBITTORRENT_URL")
    username = os.getenv("QBITTORRENT_USER")
    password = os.getenv("QBITTORRENT_PASS")

    if not base_url:
        print(
            "Error: QBITTORRENT_URL environment variable must be set.", file=sys.stderr
        )
        raise typer.Exit(code=1)

    return QBitClient(base_url, username, password)


# Application
@app.command()
def info(pretty: bool = typer.Option(False, "--pretty")):
    """Get global transfer information."""
    client = get_client()
    try:
        data = client.get_transfer_info()
        echo_json(data, pretty=pretty)
    except Exception as e:
        print(f"Error fetching transfer info: {e}", file=sys.stderr)
        raise typer.Exit(code=1)


@app.command()
def app_info(pretty: bool = typer.Option(False, "--pretty")):
    """Get application and API version."""
    client = get_client()
    try:
        data = {
            "app_version": client.get_app_version(),
            "api_version": client.get_api_version(),
        }
        echo_json(data, pretty=pretty)
    except Exception as e:
        print(f"Error fetching app info: {e}", file=sys.stderr)
        raise typer.Exit(code=1)


@app.command()
def prefs(pretty: bool = typer.Option(False, "--pretty")):
    """Get application preferences."""
    client = get_client()
    try:
        data = client.get_preferences()
        echo_json(data, pretty=pretty)
    except Exception as e:
        print(f"Error fetching preferences: {e}", file=sys.stderr)
        raise typer.Exit(code=1)


# Log
@app.command()
def log(
    last_id: int = typer.Option(-1, "--last-id"),
    pretty: bool = typer.Option(False, "--pretty"),
):
    """Get application log."""
    client = get_client()
    try:
        data = client.get_log(last_known_id=last_id)
        echo_json(data, pretty=pretty)
    except Exception as e:
        print(f"Error fetching log: {e}", file=sys.stderr)
        raise typer.Exit(code=1)


# Torrent management
@app.command()
def list_torrents(
    filter_type: Optional[str] = typer.Option(None, "--filter", "-f"),
    category: Optional[str] = typer.Option(None, "--category", "-c"),
    pretty: bool = typer.Option(False, "--pretty"),
):
    """List all torrents with optional filtering."""
    client = get_client()
    try:
        torrents = client.get_torrents(filter_type=filter_type, category=category)
        echo_json(torrents, pretty=pretty)
    except Exception as e:
        print(f"Error listing torrents: {e}", file=sys.stderr)
        raise typer.Exit(code=1)


@app.command()
def add(urls: List[str], pretty: bool = typer.Option(False, "--pretty")):
    """Add one or more magnet/torrent URLs to the queue."""
    client = get_client()
    try:
        success = client.add_torrent(urls)
        echo_json({"status": "success" if success else "failed"}, pretty=pretty)
    except Exception as e:
        print(f"Error adding torrents: {e}", file=sys.stderr)
        raise typer.Exit(code=1)


@app.command()
def pause(hashes: List[str], pretty: bool = typer.Option(False, "--pretty")):
    """Pause one or more torrents by their hash."""
    client = get_client()
    try:
        success = client.pause_torrents(hashes)
        echo_json({"status": "success" if success else "failed"}, pretty=pretty)
    except Exception as e:
        print(f"Error pausing torrents: {e}", file=sys.stderr)
        raise typer.Exit(code=1)


@app.command()
def resume(hashes: List[str], pretty: bool = typer.Option(False, "--pretty")):
    """Resume one or more torrents by their hash."""
    client = get_client()
    try:
        success = client.resume_torrents(hashes)
        echo_json({"status": "success" if success else "failed"}, pretty=pretty)
    except Exception as e:
        print(f"Error resuming torrents: {e}", file=sys.stderr)
        raise typer.Exit(code=1)


@app.command()
def delete(
    hashes: List[str],
    delete_files: bool = typer.Option(False, "--delete-files"),
    pretty: bool = typer.Option(False, "--pretty"),
):
    """Delete one or more torrents."""
    client = get_client()
    try:
        success = client.delete_torrents(hashes, delete_files=delete_files)
        echo_json({"status": "success" if success else "failed"}, pretty=pretty)
    except Exception as e:
        print(f"Error deleting torrents: {e}", file=sys.stderr)
        raise typer.Exit(code=1)


# Search
@app.command()
def search(
    pattern: str, category: str = "all", pretty: bool = typer.Option(False, "--pretty")
):
    """Start a search for torrents."""
    client = get_client()
    try:
        data = client.search_start(pattern, category=category)
        echo_json(data, pretty=pretty)
    except Exception as e:
        print(f"Error starting search: {e}", file=sys.stderr)
        raise typer.Exit(code=1)


@app.command()
def search_results(
    search_id: int, limit: int = 10, pretty: bool = typer.Option(False, "--pretty")
):
    """Get results for a search task."""
    client = get_client()
    try:
        data = client.search_results(search_id, limit=limit)
        echo_json(data, pretty=pretty)
    except Exception as e:
        print(f"Error fetching search results: {e}", file=sys.stderr)
        raise typer.Exit(code=1)


# RSS
@app.command()
def rss(pretty: bool = typer.Option(False, "--pretty")):
    """Get RSS items."""
    client = get_client()
    try:
        data = client.get_rss_data()
        echo_json(data, pretty=pretty)
    except Exception as e:
        print(f"Error fetching RSS: {e}", file=sys.stderr)
        raise typer.Exit(code=1)


def main():
    app()


if __name__ == "__main__":
    main()
