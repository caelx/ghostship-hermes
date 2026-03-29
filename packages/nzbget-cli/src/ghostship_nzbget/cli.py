import typer
import os
import json
import sys
from typing import Optional, List, Any
from .client import NZBGetClient

app = typer.Typer(help="NZBGet CLI interface.")

def echo_json(data: Any, pretty: bool = False):
    indent = 2 if pretty else None
    typer.echo(json.dumps(data, indent=indent))

def get_client() -> NZBGetClient:
    base_url = os.getenv("NZBGET_URL")
    username = os.getenv("NZBGET_USER")
    password = os.getenv("NZBGET_PASS")
    
    if not base_url or not username or not password:
        print("Error: NZBGET_URL, NZBGET_USER, and NZBGET_PASS environment variables must be set.", file=sys.stderr)
        raise typer.Exit(code=1)
    
    return NZBGetClient(base_url, username, password)

@app.command()
def info(pretty: bool = typer.Option(False, "--pretty")):
    """Get global status information."""
    client = get_client()
    try:
        data = client.get_status()
        echo_json(data, pretty=pretty)
    except Exception as e:
        print(f"Error fetching status: {e}", file=sys.stderr)
        raise typer.Exit(code=1)

@app.command()
def version(pretty: bool = typer.Option(False, "--pretty")):
    """Get NZBGet version."""
    client = get_client()
    try:
        data = client.get_version()
        echo_json({"version": data}, pretty=pretty)
    except Exception as e:
        print(f"Error fetching version: {e}", file=sys.stderr)
        raise typer.Exit(code=1)

@app.command()
def list_queue(pretty: bool = typer.Option(False, "--pretty")):
    """List all downloads in the queue."""
    client = get_client()
    try:
        groups = client.list_groups()
        echo_json(groups, pretty=pretty)
    except Exception as e:
        print(f"Error listing queue: {e}", file=sys.stderr)
        raise typer.Exit(code=1)

@app.command()
def list_files(nzb_id: int, pretty: bool = typer.Option(False, "--pretty")):
    """List files in a specific NZB group."""
    client = get_client()
    try:
        data = client.list_files(nzb_id)
        echo_json(data, pretty=pretty)
    except Exception as e:
        print(f"Error listing files: {e}", file=sys.stderr)
        raise typer.Exit(code=1)

@app.command()
def history(pretty: bool = typer.Option(False, "--pretty")):
    """Get download history."""
    client = get_client()
    try:
        data = client.get_history()
        echo_json(data, pretty=pretty)
    except Exception as e:
        print(f"Error fetching history: {e}", file=sys.stderr)
        raise typer.Exit(code=1)

@app.command()
def add(url: str, category: str = typer.Option("", "--category", "-c"), priority: int = typer.Option(0, "--priority", "-p"), pretty: bool = typer.Option(False, "--pretty")):
    """Add an NZB URL to the queue."""
    client = get_client()
    try:
        nzbid = client.append_url(url, category=category, priority=priority)
        echo_json({"status": "success", "nzbid": nzbid}, pretty=pretty)
    except Exception as e:
        print(f"Error adding NZB: {e}", file=sys.stderr)
        raise typer.Exit(code=1)

@app.command()
def pause(pretty: bool = typer.Option(False, "--pretty")):
    """Pause NZBGet download queue."""
    client = get_client()
    try:
        success = client.pause_download()
        echo_json({"status": "success" if success else "failed"}, pretty=pretty)
    except Exception as e:
        print(f"Error pausing NZBGet: {e}", file=sys.stderr)
        raise typer.Exit(code=1)

@app.command()
def resume(pretty: bool = typer.Option(False, "--pretty")):
    """Resume NZBGet download queue."""
    client = get_client()
    try:
        success = client.resume_download()
        echo_json({"status": "success" if success else "failed"}, pretty=pretty)
    except Exception as e:
        print(f"Error resuming NZBGet: {e}", file=sys.stderr)
        raise typer.Exit(code=1)

@app.command()
def rate(limit_kb: int, pretty: bool = typer.Option(False, "--pretty")):
    """Set download speed limit in KB/s (0 for unlimited)."""
    client = get_client()
    try:
        success = client.set_rate(limit_kb)
        echo_json({"status": "success" if success else "failed"}, pretty=pretty)
    except Exception as e:
        print(f"Error setting rate: {e}", file=sys.stderr)
        raise typer.Exit(code=1)

@app.command()
def config(pretty: bool = typer.Option(False, "--pretty")):
    """Get NZBGet configuration."""
    client = get_client()
    try:
        data = client.get_config()
        echo_json(data, pretty=pretty)
    except Exception as e:
        print(f"Error fetching config: {e}", file=sys.stderr)
        raise typer.Exit(code=1)

@app.command()
def shutdown(pretty: bool = typer.Option(False, "--pretty")):
    """Shutdown NZBGet."""
    client = get_client()
    try:
        success = client.shutdown()
        echo_json({"status": "success" if success else "failed"}, pretty=pretty)
    except Exception as e:
        print(f"Error shutting down: {e}", file=sys.stderr)
        raise typer.Exit(code=1)

def main():
    app()

if __name__ == "__main__":
    main()
