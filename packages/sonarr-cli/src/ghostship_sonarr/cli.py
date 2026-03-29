import typer
import os
import json
import sys
from typing import Optional, List, Any
from .client import SonarrClient

app = typer.Typer(help="Sonarr CLI interface.")


def echo_json(data: Any, pretty: bool = False):
    indent = 2 if pretty else None
    typer.echo(json.dumps(data, indent=indent))


def get_client() -> SonarrClient:
    base_url = os.getenv("SONARR_URL")
    api_key = os.getenv("SONARR_API_KEY")
    if not base_url or not api_key:
        print(
            "Error: SONARR_URL and SONARR_API_KEY environment variables must be set.",
            file=sys.stderr,
        )
        raise typer.Exit(code=1)
    return SonarrClient(base_url, api_key)


@app.command()
def info(
    pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output"),
):
    """Get system status information."""
    client = get_client()
    try:
        data = client.get_status()
        echo_json(data, pretty=pretty)
    except Exception as e:
        print(f"Error fetching status: {e}", file=sys.stderr)
        raise typer.Exit(code=1)


@app.command()
def list_series(
    pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output"),
):
    """List all series in the library."""
    client = get_client()
    try:
        series = client.get_series()
        echo_json(series, pretty=pretty)
    except Exception as e:
        print(f"Error listing series: {e}", file=sys.stderr)
        raise typer.Exit(code=1)


@app.command()
def lookup(
    term: str,
    pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output"),
):
    """Search for new series."""
    client = get_client()
    try:
        results = client.lookup_series(term)
        echo_json(results, pretty=pretty)
    except Exception as e:
        print(f"Error searching series: {e}", file=sys.stderr)
        raise typer.Exit(code=1)


@app.command()
def get_series(
    series_id: int,
    pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output"),
):
    """Get detailed information for a specific series."""
    client = get_client()
    try:
        data = client.get_series(series_id)
        echo_json(data, pretty=pretty)
    except Exception as e:
        print(f"Error fetching series {series_id}: {e}", file=sys.stderr)
        raise typer.Exit(code=1)


@app.command()
def history(
    page: int = 1,
    page_size: int = 10,
    pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output"),
):
    """View history of downloads and imports."""
    client = get_client()
    try:
        data = client.get_history(page=page, page_size=page_size)
        echo_json(data, pretty=pretty)
    except Exception as e:
        print(f"Error fetching history: {e}", file=sys.stderr)
        raise typer.Exit(code=1)


@app.command()
def queue(
    pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output"),
):
    """View current download queue."""
    client = get_client()
    try:
        data = client.get_queue()
        echo_json(data, pretty=pretty)
    except Exception as e:
        print(f"Error fetching queue: {e}", file=sys.stderr)
        raise typer.Exit(code=1)


@app.command()
def command(
    name: str,
    args: Optional[str] = typer.Option(
        None, "--args", help="JSON string of arguments for the command"
    ),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output"),
):
    """Run a long-running command (e.g., RescanSeries, EpisodeSearch)."""
    client = get_client()
    try:
        kwargs = json.loads(args) if args else {}
        result = client.run_command(name, **kwargs)
        echo_json(result, pretty=pretty)
    except Exception as e:
        print(f"Error running command {name}: {e}", file=sys.stderr)
        raise typer.Exit(code=1)


@app.command()
def add(
    tvdb_id: int,
    title: str,
    quality_profile_id: int = 1,
    language_profile_id: int = 1,
    root_folder_path: str = "/tv",
    monitored: bool = True,
    pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output"),
):
    """Add a new series to the library."""
    client = get_client()
    try:
        series_data = {
            "title": title,
            "tvdbId": tvdb_id,
            "qualityProfileId": quality_profile_id,
            "languageProfileId": language_profile_id,
            "rootFolderPath": root_folder_path,
            "monitored": monitored,
            "addOptions": {"searchForMissingEpisodes": True},
        }
        result = client.add_series(series_data)
        echo_json(result, pretty=pretty)
    except Exception as e:
        print(f"Error adding series: {e}", file=sys.stderr)
        raise typer.Exit(code=1)


@app.command()
def missing(
    page: int = 1,
    page_size: int = 10,
    pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output"),
):
    """List missing episodes."""
    client = get_client()
    try:
        data = client.get_wanted_missing(page=page, page_size=page_size)
        echo_json(data, pretty=pretty)
    except Exception as e:
        print(f"Error fetching missing episodes: {e}", file=sys.stderr)
        raise typer.Exit(code=1)


@app.command()
def blocklist(
    page: int = 1,
    page_size: int = 10,
    pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output"),
):
    """List blocklisted releases."""
    client = get_client()
    try:
        data = client.get_blocklist(page=page, page_size=page_size)
        echo_json(data, pretty=pretty)
    except Exception as e:
        print(f"Error fetching blocklist: {e}", file=sys.stderr)
        raise typer.Exit(code=1)


@app.command()
def tags(
    pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output"),
):
    """List all tags."""
    client = get_client()
    try:
        data = client.get_tags()
        echo_json(data, pretty=pretty)
    except Exception as e:
        print(f"Error fetching tags: {e}", file=sys.stderr)
        raise typer.Exit(code=1)


@app.command()
def rootfolders(
    pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output"),
):
    """List root folders."""
    client = get_client()
    try:
        data = client.get_root_folders()
        echo_json(data, pretty=pretty)
    except Exception as e:
        print(f"Error fetching root folders: {e}", file=sys.stderr)
        raise typer.Exit(code=1)


@app.command()
def profiles(
    pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output"),
):
    """List quality profiles."""
    client = get_client()
    try:
        data = client.get_quality_profiles()
        echo_json(data, pretty=pretty)
    except Exception as e:
        print(f"Error fetching profiles: {e}", file=sys.stderr)
        raise typer.Exit(code=1)


def main():
    app()


if __name__ == "__main__":
    main()
