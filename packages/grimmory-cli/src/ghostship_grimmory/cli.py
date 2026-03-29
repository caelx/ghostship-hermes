import typer
import os
import json
import sys
from typing import Optional, List, Any
from .client import GrimmoryClient

app = typer.Typer(help="Grimmory (Book Manager) CLI interface.")

def echo_json(data: Any, pretty: bool = False):
    indent = 2 if pretty else None
    typer.echo(json.dumps(data, indent=indent))

def get_client() -> GrimmoryClient:
    base_url = os.getenv("GRIMMORY_URL")
    token = os.getenv("GRIMMORY_TOKEN")
    
    if not base_url or not token:
        print("Error: GRIMMORY_URL and GRIMMORY_TOKEN environment variables must be set.", file=sys.stderr)
        raise typer.Exit(code=1)
    
    return GrimmoryClient(base_url, token)

@app.command()
def info(pretty: bool = typer.Option(False, "--pretty")):
    """Get system version information."""
    client = get_client()
    try:
        data = client.get_version()
        echo_json(data, pretty=pretty)
    except Exception as e:
        echo_json({"error": str(e)}, pretty=pretty)
        raise typer.Exit(code=1)

@app.command()
def list_books(page: int = 0, size: int = 20, library_id: Optional[int] = None, pretty: bool = typer.Option(False, "--pretty")):
    """List books in the library."""
    client = get_client()
    try:
        data = client.get_books(page=page, size=size, library_id=library_id)
        echo_json(data, pretty=pretty)
    except Exception as e:
        echo_json({"error": str(e)}, pretty=pretty)
        raise typer.Exit(code=1)

@app.command()
def get_book(book_id: int, pretty: bool = typer.Option(False, "--pretty")):
    """Get detailed information for a book."""
    client = get_client()
    try:
        data = client.get_book(book_id)
        echo_json(data, pretty=pretty)
    except Exception as e:
        echo_json({"error": str(e)}, pretty=pretty)
        raise typer.Exit(code=1)

@app.command()
def list_libraries(pretty: bool = typer.Option(False, "--pretty")):
    """List all configured libraries."""
    client = get_client()
    try:
        data = client.get_libraries()
        echo_json(data, pretty=pretty)
    except Exception as e:
        echo_json({"error": str(e)}, pretty=pretty)
        raise typer.Exit(code=1)

@app.command()
def scan(pretty: bool = typer.Option(False, "--pretty")):
    """Trigger a scan of all libraries."""
    client = get_client()
    try:
        data = client.scan_libraries()
        echo_json(data, pretty=pretty)
    except Exception as e:
        echo_json({"error": str(e)}, pretty=pretty)
        raise typer.Exit(code=1)

@app.command()
def list_authors(page: int = 0, size: int = 20, pretty: bool = typer.Option(False, "--pretty")):
    """List authors."""
    client = get_client()
    try:
        data = client.get_authors(page=page, size=size)
        echo_json(data, pretty=pretty)
    except Exception as e:
        echo_json({"error": str(e)}, pretty=pretty)
        raise typer.Exit(code=1)

@app.command()
def list_shelves(pretty: bool = typer.Option(False, "--pretty")):
    """List all shelves."""
    client = get_client()
    try:
        data = client.get_shelves()
        echo_json(data, pretty=pretty)
    except Exception as e:
        echo_json({"error": str(e)}, pretty=pretty)
        raise typer.Exit(code=1)

@app.command()
def list_tasks(pretty: bool = typer.Option(False, "--pretty")):
    """List active system tasks."""
    client = get_client()
    try:
        data = client.get_tasks()
        echo_json(data, pretty=pretty)
    except Exception as e:
        echo_json({"error": str(e)}, pretty=pretty)
        raise typer.Exit(code=1)

def main():
    app()

if __name__ == "__main__":
    main()
