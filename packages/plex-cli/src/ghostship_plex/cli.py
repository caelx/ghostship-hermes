import typer
import os
import json
import sys
from typing import Optional, List, Any
from .client import PlexClient

app = typer.Typer(help="Plex Media Server CLI interface.")

def echo_json(data: Any, pretty: bool = False):
    indent = 2 if pretty else None
    typer.echo(json.dumps(data, indent=indent))

def get_client() -> PlexClient:
    base_url = os.getenv("PLEX_URL")
    token = os.getenv("PLEX_TOKEN")
    if not base_url or not token:
        print("Error: PLEX_URL and PLEX_TOKEN environment variables must be set.", file=sys.stderr)
        raise typer.Exit(code=1)
    return PlexClient(base_url, token)

@app.command()
def info(pretty: bool = typer.Option(False, "--pretty")):
    """Get server identity and status information."""
    client = get_client()
    try:
        data = {
            "identity": client.get_identity().get("MediaContainer", {}),
            "server": client.get_server_info().get("MediaContainer", {})
        }
        echo_json(data, pretty=pretty)
    except Exception as e:
        print(f"Error fetching info: {e}", file=sys.stderr)
        raise typer.Exit(code=1)

@app.command()
def libraries(pretty: bool = typer.Option(False, "--pretty")):
    """List all library sections on the server."""
    client = get_client()
    try:
        data = client.get_library_sections().get("MediaContainer", {}).get("Directory", [])
        echo_json(data, pretty=pretty)
    except Exception as e:
        print(f"Error fetching libraries: {e}", file=sys.stderr)
        raise typer.Exit(code=1)

@app.command()
def library(section_id: int, pretty: bool = typer.Option(False, "--pretty")):
    """List all items in a library section."""
    client = get_client()
    try:
        data = client.get_library_section(section_id).get("MediaContainer", {}).get("Metadata", [])
        echo_json(data, pretty=pretty)
    except Exception as e:
        print(f"Error fetching library {section_id}: {e}", file=sys.stderr)
        raise typer.Exit(code=1)

@app.command()
def refresh(section_id: Optional[int] = typer.Option(None, "--id", help="Library section ID"), pretty: bool = typer.Option(False, "--pretty")):
    """Refresh one or all libraries."""
    client = get_client()
    try:
        client.refresh_library(section_id)
        echo_json({"status": "success", "section_id": section_id}, pretty=pretty)
    except Exception as e:
        print(f"Error refreshing libraries: {e}", file=sys.stderr)
        raise typer.Exit(code=1)

@app.command()
def sessions(pretty: bool = typer.Option(False, "--pretty")):
    """View active media playback sessions."""
    client = get_client()
    try:
        data = client.get_status_sessions().get("MediaContainer", {}).get("Metadata", [])
        echo_json(data, pretty=pretty)
    except Exception as e:
        print(f"Error fetching sessions: {e}", file=sys.stderr)
        raise typer.Exit(code=1)

@app.command()
def metadata(rating_key: int, children: bool = typer.Option(False, "--children"), pretty: bool = typer.Option(False, "--pretty")):
    """Get metadata for a specific media item."""
    client = get_client()
    try:
        if children:
            data = client.get_metadata_children(rating_key).get("MediaContainer", {}).get("Metadata", [])
        else:
            data = client.get_metadata(rating_key).get("MediaContainer", {}).get("Metadata", [{}])[0]
        echo_json(data, pretty=pretty)
    except Exception as e:
        print(f"Error fetching metadata {rating_key}: {e}", file=sys.stderr)
        raise typer.Exit(code=1)

@app.command()
def playlists(pretty: bool = typer.Option(False, "--pretty")):
    """List all playlists."""
    client = get_client()
    try:
        data = client.get_playlists().get("MediaContainer", {}).get("Metadata", [])
        echo_json(data, pretty=pretty)
    except Exception as e:
        print(f"Error fetching playlists: {e}", file=sys.stderr)
        raise typer.Exit(code=1)

@app.command()
def collections(section_id: int, pretty: bool = typer.Option(False, "--pretty")):
    """List collections in a library section."""
    client = get_client()
    try:
        data = client.get_collections(section_id).get("MediaContainer", {}).get("Metadata", [])
        echo_json(data, pretty=pretty)
    except Exception as e:
        print(f"Error fetching collections for section {section_id}: {e}", file=sys.stderr)
        raise typer.Exit(code=1)

@app.command()
def prefs(pretty: bool = typer.Option(False, "--pretty")):
    """Get server preferences."""
    client = get_client()
    try:
        data = client.get_preferences().get("MediaContainer", {}).get("Setting", [])
        echo_json(data, pretty=pretty)
    except Exception as e:
        print(f"Error fetching preferences: {e}", file=sys.stderr)
        raise typer.Exit(code=1)

@app.command()
def tasks(pretty: bool = typer.Option(False, "--pretty")):
    """List scheduled maintenance (Butler) tasks."""
    client = get_client()
    try:
        data = client.get_butler_tasks().get("MediaContainer", {}).get(" butlerTask", [])
        echo_json(data, pretty=pretty)
    except Exception as e:
        print(f"Error fetching butler tasks: {e}", file=sys.stderr)
        raise typer.Exit(code=1)

def main():
    app()

if __name__ == "__main__":
    main()
