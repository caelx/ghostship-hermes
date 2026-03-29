import typer
import os
import json
import sys
from typing import Optional, List, Any
from .client import TautulliClient

app = typer.Typer(help="Tautulli CLI interface.")

def echo_json(data: Any, pretty: bool = False):
    indent = 2 if pretty else None
    typer.echo(json.dumps(data, indent=indent))

def get_client() -> TautulliClient:
    base_url = os.getenv("TAUTULLI_URL")
    api_key = os.getenv("TAUTULLI_API_KEY")
    
    if not base_url or not api_key:
        print("Error: TAUTULLI_URL and TAUTULLI_API_KEY environment variables must be set.", file=sys.stderr)
        raise typer.Exit(code=1)
    
    return TautulliClient(base_url, api_key)

@app.command()
def info(pretty: bool = typer.Option(False, "--pretty")):
    """Get Tautulli server information."""
    client = get_client()
    try:
        data = {
            "tautulli": client.get_tautulli_info(),
            "server_status": client.get_server_status()
        }
        echo_json(data, pretty=pretty)
    except Exception as e:
        print(f"Error fetching info: {e}", file=sys.stderr)
        raise typer.Exit(code=1)

@app.command()
def activity(pretty: bool = typer.Option(False, "--pretty")):
    """Get current streaming activity."""
    client = get_client()
    try:
        data = client.get_activity()
        echo_json(data, pretty=pretty)
    except Exception as e:
        print(f"Error fetching activity: {e}", file=sys.stderr)
        raise typer.Exit(code=1)

@app.command()
def history(page: int = 1, length: int = 10, search: Optional[str] = None, pretty: bool = typer.Option(False, "--pretty")):
    """Get playback history."""
    client = get_client()
    try:
        data = client.get_history(page=page, length=length, search=search)
        echo_json(data, pretty=pretty)
    except Exception as e:
        print(f"Error fetching history: {e}", file=sys.stderr)
        raise typer.Exit(code=1)

@app.command()
def users(pretty: bool = typer.Option(False, "--pretty")):
    """Get all users."""
    client = get_client()
    try:
        data = client.get_users()
        echo_json(data, pretty=pretty)
    except Exception as e:
        print(f"Error fetching users: {e}", file=sys.stderr)
        raise typer.Exit(code=1)

@app.command()
def user_stats(user_id: int, pretty: bool = typer.Option(False, "--pretty")):
    """Get statistics for a specific user."""
    client = get_client()
    try:
        data = {
            "player_stats": client.get_user_player_stats(user_id),
            "watch_time_stats": client.get_user_watch_time_stats(user_id)
        }
        echo_json(data, pretty=pretty)
    except Exception as e:
        print(f"Error fetching user stats for {user_id}: {e}", file=sys.stderr)
        raise typer.Exit(code=1)

@app.command()
def libraries(pretty: bool = typer.Option(False, "--pretty")):
    """Get all libraries."""
    client = get_client()
    try:
        data = client.get_libraries()
        echo_json(data, pretty=pretty)
    except Exception as e:
        print(f"Error fetching libraries: {e}", file=sys.stderr)
        raise typer.Exit(code=1)

@app.command()
def search(query: str, limit: int = 10, pretty: bool = typer.Option(False, "--pretty")):
    """Search for media via Tautulli."""
    client = get_client()
    try:
        data = client.search(query, limit=limit)
        echo_json(data, pretty=pretty)
    except Exception as e:
        print(f"Error searching: {e}", file=sys.stderr)
        raise typer.Exit(code=1)

@app.command()
def terminate(session_id: str, message: Optional[str] = None, pretty: bool = typer.Option(False, "--pretty")):
    """Terminate a streaming session."""
    client = get_client()
    try:
        data = client.terminate_session(session_id, message=message)
        echo_json(data, pretty=pretty)
    except Exception as e:
        print(f"Error terminating session {session_id}: {e}", file=sys.stderr)
        raise typer.Exit(code=1)

def main():
    app()

if __name__ == "__main__":
    main()
