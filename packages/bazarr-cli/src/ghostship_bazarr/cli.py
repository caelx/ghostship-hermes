import typer
import os
import json
import sys
from typing import Optional, List, Any
from .client import BazarrClient

app = typer.Typer(help="Bazarr CLI interface.")


def echo_json(data: Any, pretty: bool = False):
    indent = 2 if pretty else None
    typer.echo(json.dumps(data, indent=indent))


def get_client() -> BazarrClient:
    base_url = os.getenv("BAZARR_URL")
    api_key = os.getenv("BAZARR_API_KEY")

    if not base_url or not api_key:
        print(
            "Error: BAZARR_URL and BAZARR_API_KEY environment variables must be set.",
            file=sys.stderr,
        )
        raise typer.Exit(code=1)

    return BazarrClient(base_url, api_key)


@app.command()
def info(
    pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output"),
):
    """Get system status information."""
    client = get_client()
    try:
        data = client.get_system_status()
        echo_json(data, pretty=pretty)
    except Exception as e:
        print(f"Error fetching status: {e}", file=sys.stderr)
        raise typer.Exit(code=1)


@app.command()
def badges(
    pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output"),
):
    """Get badges count to update the UI."""
    client = get_client()
    try:
        data = client.get_badges()
        echo_json(data, pretty=pretty)
    except Exception as e:
        print(f"Error fetching badges: {e}", file=sys.stderr)
        raise typer.Exit(code=1)


@app.command()
def episodes(
    series_id: Optional[int] = typer.Option(
        None, "--series-id", help="Filter by series ID"
    ),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output"),
):
    """List episodes metadata."""
    client = get_client()
    try:
        data = client.get_episodes(series_id=series_id)
        echo_json(data, pretty=pretty)
    except Exception as e:
        print(f"Error fetching episodes: {e}", file=sys.stderr)
        raise typer.Exit(code=1)


@app.command()
def wanted_episodes(
    pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output"),
):
    """List wanted episodes."""
    client = get_client()
    try:
        data = client.get_wanted_episodes()
        echo_json(data, pretty=pretty)
    except Exception as e:
        print(f"Error fetching wanted episodes: {e}", file=sys.stderr)
        raise typer.Exit(code=1)


@app.command()
def movies(
    pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output"),
):
    """List all movies."""
    client = get_client()
    try:
        data = client.get_movies()
        echo_json(data, pretty=pretty)
    except Exception as e:
        print(f"Error fetching movies: {e}", file=sys.stderr)
        raise typer.Exit(code=1)


@app.command()
def wanted_movies(
    pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output"),
):
    """List wanted movies."""
    client = get_client()
    try:
        data = client.get_wanted_movies()
        echo_json(data, pretty=pretty)
    except Exception as e:
        print(f"Error fetching wanted movies: {e}", file=sys.stderr)
        raise typer.Exit(code=1)


@app.command()
def series(
    pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output"),
):
    """List all series."""
    client = get_client()
    try:
        data = client.get_series()
        echo_json(data, pretty=pretty)
    except Exception as e:
        print(f"Error fetching series: {e}", file=sys.stderr)
        raise typer.Exit(code=1)


@app.command()
def providers(
    pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output"),
):
    """List all providers."""
    client = get_client()
    try:
        data = client.get_providers()
        echo_json(data, pretty=pretty)
    except Exception as e:
        print(f"Error fetching providers: {e}", file=sys.stderr)
        raise typer.Exit(code=1)


@app.command()
def subtitles(
    pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output"),
):
    """List all subtitles."""
    client = get_client()
    try:
        data = client.get_subtitles()
        echo_json(data, pretty=pretty)
    except Exception as e:
        print(f"Error fetching subtitles: {e}", file=sys.stderr)
        raise typer.Exit(code=1)


@app.command()
def health(
    pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output"),
):
    """Get system health information."""
    client = get_client()
    try:
        data = client.get_system_health()
        echo_json(data, pretty=pretty)
    except Exception as e:
        print(f"Error fetching health: {e}", file=sys.stderr)
        raise typer.Exit(code=1)


@app.command()
def jobs(
    pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output"),
):
    """List system jobs."""
    client = get_client()
    try:
        data = client.get_system_jobs()
        echo_json(data, pretty=pretty)
    except Exception as e:
        print(f"Error fetching jobs: {e}", file=sys.stderr)
        raise typer.Exit(code=1)


@app.command()
def tasks(
    pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output"),
):
    """List system tasks."""
    client = get_client()
    try:
        data = client.get_system_tasks()
        echo_json(data, pretty=pretty)
    except Exception as e:
        print(f"Error fetching tasks: {e}", file=sys.stderr)
        raise typer.Exit(code=1)


@app.command()
def search_missing():
    """Trigger search for missing subtitles."""
    client = get_client()
    try:
        data = client.search_subtitles_missing()
        echo_json(data)
    except Exception as e:
        print(f"Error triggering search: {e}", file=sys.stderr)
        raise typer.Exit(code=1)


@app.command()
def history(
    media: str = typer.Option("episodes", "--media", help="episodes or movies"),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output"),
):
    """Get subtitle download history."""
    client = get_client()
    try:
        if media == "movies":
            data = client.get_movies_history()
        else:
            data = client.get_episodes_history()
        echo_json(data, pretty=pretty)
    except Exception as e:
        print(f"Error fetching history: {e}", file=sys.stderr)
        raise typer.Exit(code=1)


@app.command()
def blacklist(
    media: str = typer.Option("episodes", "--media", help="episodes or movies"),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output"),
):
    """Get blocklisted subtitles."""
    client = get_client()
    try:
        if media == "movies":
            data = client.get_movies_blacklist()
        else:
            data = client.get_episodes_blacklist()
        echo_json(data, pretty=pretty)
    except Exception as e:
        print(f"Error fetching blacklist: {e}", file=sys.stderr)
        raise typer.Exit(code=1)


def main():
    app()


if __name__ == "__main__":
    main()
