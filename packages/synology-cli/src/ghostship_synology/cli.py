import typer
import os
import json
import sys
from typing import Optional, List, Any
from .client import SynologyClient

app = typer.Typer(help="Synology File Station CLI interface.")

def echo_json(data: Any, pretty: bool = False):
    indent = 2 if pretty else None
    typer.echo(json.dumps(data, indent=indent))

def get_client() -> SynologyClient:
    base_url = os.getenv("SYNOLOGY_URL")
    username = os.getenv("SYNOLOGY_USER")
    password = os.getenv("SYNOLOGY_PASS")
    verify_ssl = os.getenv("SYNOLOGY_VERIFY_SSL", "true").lower() == "true"
    
    if not base_url or not username or not password:
        print("Error: SYNOLOGY_URL, SYNOLOGY_USER, and SYNOLOGY_PASS environment variables must be set.", file=sys.stderr)
        raise typer.Exit(code=1)
    
    client = SynologyClient(base_url, username, password, verify_ssl)
    try:
        client.login()
    except Exception as e:
        print(f"Login failed: {e}", file=sys.stderr)
        raise typer.Exit(code=1)
    return client

@app.command()
def list_shares(pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output")):
    """List all shared folders on the NAS."""
    client = get_client()
    try:
        shares = client.list_shares().get("shares", [])
        echo_json(shares, pretty=pretty)
    finally:
        client.logout()

@app.command()
def list_files(path: str, offset: int = 0, limit: int = 100, pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output")):
    """List files and folders in a specific path."""
    client = get_client()
    try:
        data = client.list_files(path, offset=offset, limit=limit)
        files = data.get("files", [])
        echo_json(files, pretty=pretty)
    finally:
        client.logout()

@app.command()
def download(path: str, output: str = typer.Option(".", "--output", "-o", help="Output directory or file path"), pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output")):
    """Download a file from the NAS."""
    client = get_client()
    try:
        response = client.download_file(path)
        filename = os.path.basename(path)
        dest = os.path.join(output, filename) if os.path.isdir(output) else output
        
        with open(dest, "wb") as f:
            f.write(response.content)
        echo_json({"status": "success", "message": f"Successfully downloaded {path} to {dest}"}, pretty=pretty)
    finally:
        client.logout()

@app.command()
def info(path: str, pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output")):
    """Get detailed information for a file or folder."""
    client = get_client()
    try:
        data = client.get_file_info(path)
        echo_json(data, pretty=pretty)
    finally:
        client.logout()

@app.command()
def search(folder_path: str, pattern: str, recursive: bool = True, pretty: bool = typer.Option(False, "--pretty")):
    """Start a search for files."""
    client = get_client()
    try:
        taskid = client.search_start(folder_path, pattern, recursive=recursive)
        echo_json({"status": "started", "taskid": taskid}, pretty=pretty)
    finally:
        client.logout()

@app.command()
def search_results(taskid: str, offset: int = 0, limit: int = 100, pretty: bool = typer.Option(False, "--pretty")):
    """Get search results for a task."""
    client = get_client()
    try:
        data = client.search_list(taskid, offset=offset, limit=limit)
        echo_json(data, pretty=pretty)
    finally:
        client.logout()

@app.command()
def mkdir(path: str, name: str, parents: bool = typer.Option(False, "--parents", "-p"), pretty: bool = typer.Option(False, "--pretty")):
    """Create a new folder."""
    client = get_client()
    try:
        data = client.create_folder(path, name, force_parent=parents)
        echo_json(data, pretty=pretty)
    finally:
        client.logout()

@app.command()
def rename(path: str, name: str, pretty: bool = typer.Option(False, "--pretty")):
    """Rename a file or folder."""
    client = get_client()
    try:
        data = client.rename(path, name)
        echo_json(data, pretty=pretty)
    finally:
        client.logout()

@app.command()
def rm(path: str, recursive: bool = typer.Option(True, "--recursive/--no-recursive"), pretty: bool = typer.Option(False, "--pretty")):
    """Delete a file or folder."""
    client = get_client()
    try:
        taskid = client.delete(path, recursive=recursive)
        echo_json({"status": "started", "taskid": taskid}, pretty=pretty)
    finally:
        client.logout()

def main():
    app()

if __name__ == "__main__":
    main()
