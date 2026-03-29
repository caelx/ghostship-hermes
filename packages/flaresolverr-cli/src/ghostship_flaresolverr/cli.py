import json
import os
import sys
import typer
from typing import Optional, Any
from .client import FlareSolverrClient

app = typer.Typer(help="FlareSolverr CLI interface.")


def echo_json(data: Any, pretty: bool = False):
    indent = 2 if pretty else None
    typer.echo(json.dumps(data, indent=indent))


def get_client() -> FlareSolverrClient:
    base_url = os.getenv("FLARESOLVERR_URL")
    if not base_url:
        print(
            "Error: FLARESOLVERR_URL environment variable must be set.", file=sys.stderr
        )
        raise typer.Exit(code=1)
    return FlareSolverrClient(base_url)


@app.command()
def get(
    url: str,
    session: Optional[str] = typer.Option(None, "--session"),
    pretty: bool = typer.Option(False, "--pretty"),
):
    """Perform a GET request via FlareSolverr."""
    client = get_client()
    try:
        data = client.request_get(url, session=session)
        echo_json(data, pretty=pretty)
    except Exception as e:
        echo_json({"error": str(e)}, pretty=pretty)
        raise typer.Exit(code=1)


@app.command()
def post(
    url: str,
    post_data: str,
    session: Optional[str] = typer.Option(None, "--session"),
    pretty: bool = typer.Option(False, "--pretty"),
):
    """Perform a POST request via FlareSolverr."""
    client = get_client()
    try:
        data = client.request_post(url, post_data, session=session)
        echo_json(data, pretty=pretty)
    except Exception as e:
        echo_json({"error": str(e)}, pretty=pretty)
        raise typer.Exit(code=1)


@app.command()
def create_session(
    session: Optional[str] = typer.Option(None, "--session"),
    pretty: bool = typer.Option(False, "--pretty"),
):
    """Create a new FlareSolverr session."""
    client = get_client()
    try:
        data = client.sessions_create(session=session)
        echo_json(data, pretty=pretty)
    except Exception as e:
        echo_json({"error": str(e)}, pretty=pretty)
        raise typer.Exit(code=1)


@app.command()
def list_sessions(pretty: bool = typer.Option(False, "--pretty")):
    """List all FlareSolverr sessions."""
    client = get_client()
    try:
        data = client.sessions_list()
        echo_json(data, pretty=pretty)
    except Exception as e:
        echo_json({"error": str(e)}, pretty=pretty)
        raise typer.Exit(code=1)


@app.command()
def destroy_session(session: str, pretty: bool = typer.Option(False, "--pretty")):
    """Destroy a FlareSolverr session."""
    client = get_client()
    try:
        data = client.sessions_destroy(session)
        echo_json(data, pretty=pretty)
    except Exception as e:
        echo_json({"error": str(e)}, pretty=pretty)
        raise typer.Exit(code=1)


def main():
    app()


if __name__ == "__main__":
    main()
