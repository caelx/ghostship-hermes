import typer
import os
import json
import sys
from typing import Optional, List, Any
from .client import OnyxClient

app = typer.Typer(help="Onyx CLI interface for RAG and Chat.")

def echo_json(data: Any, pretty: bool = False):
    indent = 2 if pretty else None
    typer.echo(json.dumps(data, indent=indent))

def get_client() -> OnyxClient:
    base_url = os.getenv("ONYX_URL")
    api_key = os.getenv("ONYX_API_KEY")
    if not base_url or not api_key:
        print("Error: ONYX_URL and ONYX_API_KEY environment variables must be set.", file=sys.stderr)
        raise typer.Exit(code=1)
    return OnyxClient(base_url, api_key)

@app.command()
def ingest(
    identifier: str,
    text: str,
    source: str = "file",
    cc_pair_id: Optional[int] = None,
    doc_id: Optional[str] = None,
    link: Optional[str] = None,
    metadata: Optional[str] = typer.Option(None, "--metadata", help="JSON string of metadata"),
    pretty: bool = typer.Option(False, "--pretty")
):
    """Ingest a document into Onyx."""
    client = get_client()
    try:
        meta_dict = json.loads(metadata) if metadata else {}
        document = {
            "id": doc_id,
            "semantic_identifier": identifier,
            "sections": [{"text": text, "link": link}],
            "source": source,
            "metadata": meta_dict
        }
        data = client.ingest_document(document, cc_pair_id=cc_pair_id)
        echo_json(data, pretty=pretty)
    except Exception as e:
        echo_json({"error": str(e)}, pretty=pretty)
        raise typer.Exit(code=1)

@app.command()
def chat(
    message: str,
    session_id: Optional[str] = None,
    persona_id: Optional[int] = None,
    pretty: bool = typer.Option(False, "--pretty")
):
    """Send a message to Onyx Chat."""
    client = get_client()
    try:
        kwargs: dict[str, Any] = {}
        if persona_id:
            kwargs["chat_session_info"] = {"persona_id": persona_id}
        data = client.send_chat_message(message=message, chat_session_id=session_id, **kwargs)
        echo_json(data, pretty=pretty)
    except Exception as e:
        echo_json({"error": str(e)}, pretty=pretty)
        raise typer.Exit(code=1)

@app.command()
def search(query: str, keyword: bool = typer.Option(False, "--keyword"), pretty: bool = typer.Option(False, "--pretty")):
    """Search documents in Onyx."""
    client = get_client()
    try:
        if keyword:
            data = client.keyword_search(query)
        else:
            data = client.semantic_search(query)
        echo_json(data, pretty=pretty)
    except Exception as e:
        echo_json({"error": str(e)}, pretty=pretty)
        raise typer.Exit(code=1)

@app.command()
def sessions(pretty: bool = typer.Option(False, "--pretty")):
    """List chat sessions."""
    client = get_client()
    try:
        data = client.get_chat_sessions()
        echo_json(data, pretty=pretty)
    except Exception as e:
        echo_json({"error": str(e)}, pretty=pretty)
        raise typer.Exit(code=1)

@app.command()
def delete(doc_id: str, pretty: bool = typer.Option(False, "--pretty")):
    """Delete a document from Onyx."""
    client = get_client()
    try:
        data = client.delete_document(doc_id)
        echo_json(data, pretty=pretty)
    except Exception as e:
        echo_json({"error": str(e)}, pretty=pretty)
        raise typer.Exit(code=1)

@app.command()
def history(session_id: str, pretty: bool = typer.Option(False, "--pretty")):
    """Get chat session history."""
    client = get_client()
    try:
        data = client.get_chat_history(session_id)
        echo_json(data, pretty=pretty)
    except Exception as e:
        echo_json({"error": str(e)}, pretty=pretty)
        raise typer.Exit(code=1)

def main():
    app()

if __name__ == "__main__":
    main()
