import json
from typing import Any

import httpx
import typer


app = typer.Typer(no_args_is_help=True)
search_app = typer.Typer(no_args_is_help=True)
app.add_typer(search_app, name="search")


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
    base_url: str = typer.Option("http://localhost:8080", "--base-url"),
    category: str = typer.Option("general", "--category"),
    limit: int = typer.Option(5, "--limit"),
    language: str = typer.Option("all", "--language"),
    safe_search: int = typer.Option(1, "--safe-search"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    payload = search_searxng(
        base_url=base_url,
        query=query,
        categories=category,
        limit=limit,
        language=language,
        safe_search=safe_search,
        timeout=10.0,
    )

    if json_output:
        typer.echo(json.dumps(payload))
        return

    typer.echo(f"Query: {payload['query']}")
    typer.echo(f"Results: {payload['number_of_results']}")
    for result in payload["results"]:
        typer.echo(f"- {result['title']}")
        typer.echo(f"  {result['url']}")


def main() -> None:
    app()
