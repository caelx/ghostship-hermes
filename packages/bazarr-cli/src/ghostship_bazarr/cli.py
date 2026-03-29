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
        print("Error: BAZARR_URL and BAZARR_API_KEY environment variables must be set.", file=sys.stderr)
        raise typer.Exit(code=1)
    
    return BazarrClient(base_url, api_key)

@app.command()
def info(pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output")):
    """Get system status information."""
    client = get_client()
    try:
        data = client.get_system_status()
        echo_json(data, pretty=pretty)
    except Exception as e:
        print(f"Error fetching status: {e}", file=sys.stderr)
        raise typer.Exit(code=1)

@app.command()
def list_series(pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output")):
    """List all series in the library."""
    client = get_client()
    try:
        data = client.get_series().get("data", [])
        echo_json(data, pretty=pretty)
    except Exception as e:
        print(f"Error listing series: {e}", file=sys.stderr)
        raise typer.Exit(code=1)

def main():
    app()

if __name__ == "__main__":
    main()
