from __future__ import annotations

import os
from typing import Any, Optional

import typer

from ghostship_cli_contract import DEFAULT_TIMEOUT, echo_json, require_env, run_app

from .client import KNOWN_FORMATS, RssBridgeClient, to_jsonable

app = typer.Typer(help='Typed RSS-Bridge CLI.', no_args_is_help=True)
APP_STATE = {'timeout': DEFAULT_TIMEOUT}


@app.callback()
def app_callback(timeout: float = typer.Option(DEFAULT_TIMEOUT, '--timeout', help='Hard timeout in seconds for all API calls in this invocation.')) -> None:
    APP_STATE['timeout'] = timeout


def get_client() -> RssBridgeClient:
    return RssBridgeClient(require_env('RSS_BRIDGE_URL', os.getenv('RSS_BRIDGE_URL')), timeout=APP_STATE['timeout'])


def _parse_params(values: list[str]) -> dict[str, str]:
    params: dict[str, str] = {}
    for value in values:
        if '=' not in value:
            raise typer.BadParameter(f'parameter must use key=value form: {value}')
        key, raw = value.split('=', 1)
        params[key] = raw
    return params


@app.command('list_bridges')
def list_bridges(active_only: bool = typer.Option(False, '--active-only', help='Only return bridges marked active by the instance.'), pretty: bool = typer.Option(False, '--pretty', help='Pretty print JSON output')) -> None:
    payload = get_client().list_bridges()
    if active_only:
        filtered = {name: bridge for name, bridge in payload.bridges.items() if bridge.status == 'active'}
        payload.bridges = filtered
        payload.total = len(filtered)
    echo_json(payload, pretty=pretty)


@app.command('describe_bridge')
def describe_bridge(bridge: str, context: Optional[str] = typer.Option(None, '--context', help='Optional context to focus on within the bridge schema.'), pretty: bool = typer.Option(False, '--pretty', help='Pretty print JSON output')) -> None:
    payload = get_client().get_bridge(bridge)
    if context is not None:
        data = payload.to_dict()
        data['parameters'] = {context: data['parameters'].get(context, {})}
        echo_json(data, pretty=pretty)
    else:
        echo_json(payload, pretty=pretty)


@app.command('list_contexts')
def list_contexts(bridge: str, pretty: bool = typer.Option(False, '--pretty', help='Pretty print JSON output')) -> None:
    payload = get_client().get_bridge(bridge)
    echo_json({'bridge': bridge, 'contexts': list(payload.parameters.keys())}, pretty=pretty)


@app.command('list_known_formats')
def list_known_formats(pretty: bool = typer.Option(False, '--pretty', help='Pretty print JSON output')) -> None:
    echo_json({'formats': KNOWN_FORMATS}, pretty=pretty)


@app.command('build_url')
def build_url(bridge: str = typer.Option(..., '--bridge', help='Bridge class name from action=list.'), format: str = typer.Option('Atom', '--format', help='Output format name, such as Atom, Json, or Html.'), context: Optional[str] = typer.Option(None, '--context', help='Optional named bridge context.'), param: list[str] = typer.Option([], '--param', help='Repeat key=value pairs for bridge/global parameters.'), pretty: bool = typer.Option(False, '--pretty', help='Pretty print JSON output')) -> None:
    parameters = _parse_params(param)
    url = get_client().build_display_url(bridge=bridge, format=format, context=context, parameters=parameters)
    echo_json({'url': url, 'bridge': bridge, 'format': format, 'context': context, 'parameters': parameters}, pretty=pretty)


@app.command('find_feed')
def find_feed(url: str, format: str = typer.Option('Atom', '--format', help='Format to embed in the returned display URLs.'), pretty: bool = typer.Option(False, '--pretty', help='Pretty print JSON output')) -> None:
    echo_json(get_client().find_feed(url, format=format), pretty=pretty)


@app.command('detect')
def detect(url: str, format: str = typer.Option('Atom', '--format', help='Format to embed in the redirect target.'), pretty: bool = typer.Option(False, '--pretty', help='Pretty print JSON output')) -> None:
    echo_json(get_client().detect(url, format=format), pretty=pretty)


@app.command('display')
def display(bridge: str = typer.Option(..., '--bridge', help='Bridge class name from action=list.'), format: str = typer.Option('Atom', '--format', help='Output format name, such as Atom, Json, or Html.'), context: Optional[str] = typer.Option(None, '--context', help='Optional named bridge context.'), param: list[str] = typer.Option([], '--param', help='Repeat key=value pairs for bridge/global parameters.'), pretty: bool = typer.Option(False, '--pretty', help='Pretty print JSON output')) -> None:
    echo_json(get_client().display(bridge=bridge, format=format, context=context, parameters=_parse_params(param)), pretty=pretty)


@app.command('fetch_url')
def fetch_url(url: str, pretty: bool = typer.Option(False, '--pretty', help='Pretty print JSON output')) -> None:
    echo_json(get_client().fetch_url(url), pretty=pretty)


def main() -> None:
    run_app(app)


if __name__ == '__main__':
    main()
