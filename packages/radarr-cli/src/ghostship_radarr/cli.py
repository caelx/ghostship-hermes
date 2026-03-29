import typer
import os
import json
import sys
from typing import Optional, List, Any
from .client import RadarrClient

app = typer.Typer(help="Radarr CLI interface.")

def echo_json(data: Any, pretty: bool = False):
    indent = 2 if pretty else None
    typer.echo(json.dumps(data, indent=indent))

def get_client() -> RadarrClient:
    base_url = os.getenv("RADARR_URL")
    api_key = os.getenv("RADARR_API_KEY")
    if not base_url or not api_key:
        print("Error: RADARR_URL and RADARR_API_KEY environment variables must be set.", file=sys.stderr)
        raise typer.Exit(code=1)
    return RadarrClient(base_url, api_key)

@app.command()
def info(pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output")):
    """Get system status information."""
    client = get_client()
    try:
        data = client.get_status()
        echo_json(data, pretty=pretty)
    except Exception as e:
        print(f"Error fetching status: {e}", file=sys.stderr)
        raise typer.Exit(code=1)

@app.command()
def list_movies(pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output")):
    """List all movies in the library."""
    client = get_client()
    try:
        movies = client.get_movies()
        echo_json(movies, pretty=pretty)
    except Exception as e:
        print(f"Error listing movies: {e}", file=sys.stderr)
        raise typer.Exit(code=1)

@app.command()
def lookup(term: str, pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output")):
    """Search for new movies."""
    client = get_client()
    try:
        results = client.lookup_movie(term)
        echo_json(results, pretty=pretty)
    except Exception as e:
        print(f"Error searching movies: {e}", file=sys.stderr)
        raise typer.Exit(code=1)

@app.command()
def get_movie(movie_id: int, pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output")):
    """Get detailed information for a specific movie."""
    client = get_client()
    try:
        data = client.get_movies(movie_id)
        echo_json(data, pretty=pretty)
    except Exception as e:
        print(f"Error fetching movie {movie_id}: {e}", file=sys.stderr)
        raise typer.Exit(code=1)

@app.command()
def history(page: int = 1, page_size: int = 10, pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output")):
    """View history of downloads and imports."""
    client = get_client()
    try:
        data = client.get_history(page=page, page_size=page_size)
        echo_json(data, pretty=pretty)
    except Exception as e:
        print(f"Error fetching history: {e}", file=sys.stderr)
        raise typer.Exit(code=1)

@app.command()
def queue(pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output")):
    """View current download queue."""
    client = get_client()
    try:
        data = client.get_queue()
        echo_json(data, pretty=pretty)
    except Exception as e:
        print(f"Error fetching queue: {e}", file=sys.stderr)
        raise typer.Exit(code=1)

@app.command()
def command(name: str, args: Optional[str] = typer.Option(None, "--args", help="JSON string of arguments for the command"), pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output")):
    """Run a long-running command (e.g., MoviesSearch, RescanMovie)."""
    client = get_client()
    try:
        kwargs = json.loads(args) if args else {}
        result = client.run_command(name, **kwargs)
        echo_json(result, pretty=pretty)
    except Exception as e:
        print(f"Error running command {name}: {e}", file=sys.stderr)
        raise typer.Exit(code=1)

@app.command()
def add(tmdb_id: int, title: str, quality_profile_id: int = 1, root_folder_path: str = "/movies", monitored: bool = True, pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output")):
    """Add a new movie to the library."""
    client = get_client()
    try:
        movie_data = {
            "title": title,
            "tmdbId": tmdb_id,
            "qualityProfileId": quality_profile_id,
            "rootFolderPath": root_folder_path,
            "monitored": monitored,
            "addOptions": {"searchForMovie": True}
        }
        result = client.add_movie(movie_data)
        echo_json(result, pretty=pretty)
    except Exception as e:
        print(f"Error adding movie: {e}", file=sys.stderr)
        raise typer.Exit(code=1)

def main():
    app()

if __name__ == "__main__":
    main()
