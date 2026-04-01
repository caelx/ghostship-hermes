from __future__ import annotations

import os
from typing import Any

import typer

from ghostship_cli_contract import DEFAULT_TIMEOUT, BaseHttpClient, echo_json, parse_params, require_env, run_app, run_cli_command


class SearXNGClient(BaseHttpClient):
    def build_request(self, path: str, *, params: dict[str, Any] | None = None, timeout: float | None = None):
        return self.build_request_spec('GET', path, params=params, timeout=timeout)

    def request(self, path: str, *, params: dict[str, Any] | None = None, timeout: float | None = None) -> dict[str, Any]:
        spec = self.build_request(path, params=params, timeout=timeout)
        return self.request_json(spec.method, spec.path, params=spec.params, timeout=spec.timeout)

    def search_web(self, *, query: str, category: str = 'general', limit: int = 5, language: str = 'all', safe_search: int = 1, timeout: float | None = None) -> dict[str, Any]:
        payload = self.request('search', params={'q': query, 'format': 'json', 'categories': category, 'language': language, 'safesearch': safe_search}, timeout=timeout)
        results = payload.get('results', [])[:limit]
        return {'query': query, 'number_of_results': len(results), 'results': [{'title': result.get('title', ''), 'url': result.get('url', '')} for result in results]}


app = typer.Typer(no_args_is_help=True)
APP_STATE = {'timeout': DEFAULT_TIMEOUT}


@app.callback()
def app_callback(timeout: float = typer.Option(DEFAULT_TIMEOUT, '--timeout', help='Hard timeout in seconds for all API calls in this invocation.')) -> None:
    APP_STATE['timeout'] = timeout


def get_client(base_url: str | None = None) -> SearXNGClient:
    return SearXNGClient((base_url or os.getenv('SEARXNG_URL') or 'http://localhost:8080').rstrip('/'), default_timeout=APP_STATE['timeout'])


def _emit(data: Any, pretty: bool) -> None:
    echo_json(data, pretty=pretty)


def _run(execute, *, pretty: bool) -> None:
    _emit(run_cli_command(None, execute, timeout=APP_STATE['timeout']), pretty)


def _run_request(build_request, execute, *, dry_run: bool, pretty: bool) -> None:
    _emit(run_cli_command(build_request, execute, timeout=APP_STATE['timeout'], dry_run=dry_run), pretty)


@app.command('request')
def request(path: str, param: list[str] = typer.Option([], '--param', help='Repeat key=value query parameters.'), base_url: str | None = typer.Option(None, '--base-url'), dry_run: bool = typer.Option(False, '--dry-run'), pretty: bool = typer.Option(False, '--pretty', help='Pretty print JSON output')) -> None:
    client = get_client(base_url)
    params = parse_params(param) or None
    _run_request(lambda: client.build_request(path, params=params), lambda timeout: client.request(path, params=params, timeout=timeout), dry_run=dry_run, pretty=pretty)


@app.command('search_web')
def search_web(query: str, base_url: str | None = typer.Option(None, '--base-url'), category: str = typer.Option('general', '--category'), limit: int = typer.Option(5, '--limit'), language: str = typer.Option('all', '--language'), safe_search: int = typer.Option(1, '--safe-search'), pretty: bool = typer.Option(False, '--pretty', help='Pretty print JSON output')) -> None:
    client = get_client(base_url)
    _run(lambda timeout: client.search_web(query=query, category=category, limit=limit, language=language, safe_search=safe_search, timeout=timeout), pretty=pretty)


def main() -> None:
    run_app(app)


if __name__ == '__main__':
    main()
