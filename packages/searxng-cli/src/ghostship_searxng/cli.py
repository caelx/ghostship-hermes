from __future__ import annotations

import json
import os
from typing import Any

import httpx
import typer


def _cloudflare_access_headers() -> dict[str, str]:
    headers: dict[str, str] = {}
    client_id = os.getenv("GHOSTSHIP_TEST_CF_ACCESS_CLIENT_ID")
    client_secret = os.getenv("GHOSTSHIP_TEST_CF_ACCESS_CLIENT_SECRET")
    if client_id:
        headers["CF-Access-Client-Id"] = client_id
    if client_secret:
        headers["CF-Access-Client-Secret"] = client_secret
    return headers


app = typer.Typer(no_args_is_help=True)
search_app = typer.Typer(no_args_is_help=True)
app.add_typer(search_app, name="search")


def echo_json(data: Any, pretty: bool = False):
    typer.echo(json.dumps(data, indent=2 if pretty else None))


def _parse_params(values: list[str]) -> dict[str, str]:
    params: dict[str, str] = {}
    for value in values:
        if "=" not in value:
            raise typer.BadParameter(f"parameter must use key=value form: {value}")
        key, raw = value.split("=", 1)
        params[key] = raw
    return params


def request_searxng(*, base_url: str, path: str, params: dict[str, Any] | None = None, timeout: float = 10.0) -> dict[str, Any]:
    response = httpx.get(
        f"{base_url.rstrip('/')}/{path.lstrip('/')}",
        params=params,
        timeout=timeout,
        headers=_cloudflare_access_headers(),
    )
    response.raise_for_status()
    return response.json()


def search_searxng(*, base_url: str, query: str, categories: str, limit: int, language: str, safe_search: int, timeout: float) -> dict[str, Any]:
    payload = request_searxng(
        base_url=base_url,
        path="search",
        params={
            "q": query,
            "format": "json",
            "categories": categories,
            "language": language,
            "safesearch": safe_search,
        },
        timeout=timeout,
    )
    results = payload.get("results", [])[:limit]
    return {
        "query": query,
        "number_of_results": len(results),
        "results": [{"title": result.get("title", ""), "url": result.get("url", "")} for result in results],
    }


@app.command("request")
def request(
    path: str,
    param: list[str] = typer.Option([], "--param", help="Repeat key=value query parameters."),
    base_url: str | None = typer.Option(None, "--base-url"),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output"),
) -> None:
    """Call any SearXNG JSON endpoint directly."""
    url = base_url or os.getenv("SEARXNG_URL", "http://localhost:8080")
    echo_json(request_searxng(base_url=url, path=path, params=_parse_params(param) or None), pretty=pretty)


@search_app.command("web")
def search_web(
    query: str,
    base_url: str | None = typer.Option(None, "--base-url"),
    category: str = typer.Option("general", "--category"),
    limit: int = typer.Option(5, "--limit"),
    language: str = typer.Option("all", "--language"),
    safe_search: int = typer.Option(1, "--safe-search"),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output"),
) -> None:
    url = base_url or os.getenv("SEARXNG_URL", "http://localhost:8080")
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


def main() -> None:
    app()


if __name__ == "__main__":
    main()
