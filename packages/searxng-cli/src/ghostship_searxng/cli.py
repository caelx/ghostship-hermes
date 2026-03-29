import json
import os
import sys
from typing import Any, Optional

import httpx
import typer

app = typer.Typer(no_args_is_help=True)
search_app = typer.Typer(no_args_is_help=True)
app.add_typer(search_app, name="search")

def echo_json(data: Any, pretty: bool = False):
    indent = 2 if pretty else None
    typer.echo(json.dumps(data, indent=indent))

def search_searxng(
    *,
    base_url: str,
    query: str,
    categories: str,
    limit: int,
    language: str,
    safe_search: int,
    timeout: float,
) -> dict[str, Any]:
    response = httpx.get(
        f"{base_url.rstrip('/')}/search",
        params={
            "q": query,
            "format": "json",
            "categories": categories,
            "language": language,
            "safesearch": safe_search,
        },
        timeout=timeout,
    )
    response.raise_for_status()
    payload = response.json()
    results = payload.get("results", [])[:limit]
    return {
        "query": query,
        "number_of_results": len(results),
        "results": [
            {
                "title": result.get("title", ""),
                "url": result.get("url", ""),
            }
            for result in results
        ],
    }

@search_app.command("web")
def search_web(
    query: str,
    base_url: Optional[str] = typer.Option(None, "--base-url"),
    category: str = typer.Option("general", "--category"),
    limit: int = typer.Option(5, "--limit"),
    language: str = typer.Option("all", "--language"),
    safe_search: int = typer.Option(1, "--safe-search"),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output"),
) -> None:
    url = base_url or os.getenv("SEARXNG_URL", "http://localhost:8080")
    try:
        payload = search_searxng(
            base_url=url,
            query=query,
            categories=category,
            limit=limit,
            language=language,
            safe_search=safe_search,
            timeout=10.0,
        )
        echo_json(payload, pretty=pretty)
    except Exception as e:
        echo_json({"error": str(e)}, pretty=pretty)
        raise typer.Exit(code=1)

def main() -> None:
    app()

if __name__ == "__main__":
    main()
