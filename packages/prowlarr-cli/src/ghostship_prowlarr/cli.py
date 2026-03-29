import typer
import os
import json
import sys
from typing import Optional, List, Any
from .client import ProwlarrClient

app = typer.Typer(help="Prowlarr CLI interface.")

def echo_json(data: Any, pretty: bool = False):
    indent = 2 if pretty else None
    typer.echo(json.dumps(data, indent=indent))

def get_client() -> ProwlarrClient:
    base_url = os.getenv("PROWLARR_URL")
    api_key = os.getenv("PROWLARR_API_KEY")
    if not base_url or not api_key:
        print("Error: PROWLARR_URL and PROWLARR_API_KEY environment variables must be set.", file=sys.stderr)
        raise typer.Exit(code=1)
    return ProwlarrClient(base_url, api_key)

@app.command()
def info(pretty: bool = typer.Option(False, "--pretty")):
    """Get system status information."""
    client = get_client()
    try:
        data = client.get_status()
        echo_json(data, pretty=pretty)
    except Exception as e:
        print(f"Error fetching status: {e}", file=sys.stderr)
        raise typer.Exit(code=1)

@app.command()
def list_indexers(pretty: bool = typer.Option(False, "--pretty")):
    """List all configured indexers."""
    client = get_client()
    try:
        indexers = client.get_indexers()
        echo_json(indexers, pretty=pretty)
    except Exception as e:
        print(f"Error listing indexers: {e}", file=sys.stderr)
        raise typer.Exit(code=1)

@app.command()
def search(query: str, pretty: bool = typer.Option(False, "--pretty")):
    """Search for releases across all indexers."""
    client = get_client()
    try:
        results = client.search(query)
        echo_json(results, pretty=pretty)
    except Exception as e:
        print(f"Error searching indexers: {e}", file=sys.stderr)
        raise typer.Exit(code=1)

@app.command()
def list_apps(pretty: bool = typer.Option(False, "--pretty")):
    """List connected applications (Sonarr, Radarr, etc.)."""
    client = get_client()
    try:
        apps = client.get_applications()
        echo_json(apps, pretty=pretty)
    except Exception as e:
        print(f"Error listing applications: {e}", file=sys.stderr)
        raise typer.Exit(code=1)

def main():
    app()

if __name__ == "__main__":
    main()
