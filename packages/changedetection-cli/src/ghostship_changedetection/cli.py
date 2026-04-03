from __future__ import annotations

import os
from typing import Any

import typer

from ghostship_cli_contract import (
    ConfigError,
    DEFAULT_TIMEOUT,
    echo_json,
    handle_cli_error,
    parse_json_option,
    parse_params,
    require_env,
    run_app,
    run_cli_command,
)

from .client import ChangedetectionClient

app = typer.Typer(help="Typed changedetection.io API CLI.", no_args_is_help=True)
APP_STATE = {"timeout": DEFAULT_TIMEOUT}


@app.callback()
def app_callback(timeout: float = typer.Option(DEFAULT_TIMEOUT, "--timeout", help="Hard timeout in seconds for all API calls in this invocation.")) -> None:
    APP_STATE["timeout"] = timeout


def get_client(*, require_api_key: bool = True) -> ChangedetectionClient:
    base_url = require_env("CHANGEDETECTION_URL", os.getenv("CHANGEDETECTION_URL"))
    api_key = os.getenv("CHANGEDETECTION_API_KEY")
    if require_api_key and not api_key:
        raise ConfigError("CHANGEDETECTION_API_KEY environment variable must be set")
    return ChangedetectionClient(base_url, api_key, default_timeout=APP_STATE["timeout"])


def _emit(data: Any, *, pretty: bool) -> None:
    echo_json(data, pretty=pretty)


def _run(execute, *, pretty: bool) -> None:
    try:
        result = execute(APP_STATE["timeout"])
        _emit(result, pretty=pretty)
    except Exception as exc:  # pragma: no cover
        handle_cli_error(exc)


def _run_write(build_request, execute, *, dry_run: bool, pretty: bool) -> None:
    try:
        result = run_cli_command(build_request, execute, timeout=APP_STATE["timeout"], dry_run=dry_run)
        _emit(result, pretty=pretty)
    except Exception as exc:  # pragma: no cover
        handle_cli_error(exc)


def _parse_body(body_json: str | None) -> dict[str, Any]:
    payload = parse_json_option(body_json, "--body-json")
    if not isinstance(payload, dict):
        raise ConfigError("--body-json must decode to a JSON object")
    return payload


def _parse_query_params(values: list[str]) -> dict[str, str] | None:
    params = parse_params(values)
    return params or None


@app.command("request")
def request(
    method: str,
    path: str,
    param: list[str] = typer.Option([], "--param", help="Repeat key=value query parameters."),
    body_json: str | None = typer.Option(None, "--body-json", help="Optional JSON request body."),
    body_text: str | None = typer.Option(None, "--body-text", help="Optional raw request body."),
    content_type: str | None = typer.Option(None, "--content-type", help="Optional Content-Type header."),
    accept: str | None = typer.Option(None, "--accept", help="Optional Accept header."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Print the request JSON and do not call the API."),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output"),
) -> None:
    if body_json is not None and body_text is not None:
        raise ConfigError("use either --body-json or --body-text, not both")
    params = _parse_query_params(param)
    headers = {"Content-Type": content_type, "Accept": accept}
    effective_headers = {key: value for key, value in headers.items() if value is not None} or None
    payload = parse_json_option(body_json, "--body-json")
    normalized_path = path if path.startswith("/") else f"/{path}"
    client = get_client(require_api_key=not normalized_path.endswith("/full-spec"))
    _run_write(
        lambda: client.build_request(method, path, params=params, json_data=payload, content=body_text, headers=effective_headers, timeout=APP_STATE["timeout"]),
        lambda timeout: client.request(method, path, params=params, json_data=payload, content=body_text, headers=effective_headers, timeout=timeout),
        dry_run=dry_run,
        pretty=pretty,
    )


@app.command("list_watches")
def list_watches(
    recheck_all: bool = typer.Option(False, "--recheck-all", help="Set to 1 to force recheck of all watches."),
    tag: str | None = typer.Option(None, "--tag", help="Tag name to filter results."),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output"),
) -> None:
    _run(lambda timeout: get_client().list_watches(recheck_all=recheck_all, tag=tag, timeout=timeout), pretty=pretty)


@app.command("create_watch")
def create_watch(
    body_json: str = typer.Option(..., "--body-json", help="JSON request body matching the upstream CreateWatch schema."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Print the request JSON and do not call the API."),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output"),
) -> None:
    body = _parse_body(body_json)
    client = get_client()
    _run_write(lambda: client.build_create_watch(body, timeout=APP_STATE["timeout"]), lambda timeout: client.create_watch(body, timeout=timeout), dry_run=dry_run, pretty=pretty)


@app.command("get_watch")
def get_watch(
    uuid: str,
    recheck: bool = typer.Option(False, "--recheck", help="Queue this watch for recheck."),
    paused_state: str | None = typer.Option(None, "--paused-state", help="Set pause state: paused or unpaused."),
    muted_state: str | None = typer.Option(None, "--muted-state", help="Set mute state: muted or unmuted."),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output"),
) -> None:
    _run(lambda timeout: get_client().get_watch(uuid, recheck=recheck, paused=paused_state, muted=muted_state, timeout=timeout), pretty=pretty)


@app.command("update_watch")
def update_watch(
    uuid: str,
    body_json: str = typer.Option(..., "--body-json", help="JSON request body matching the upstream UpdateWatch schema."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Print the request JSON and do not call the API."),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output"),
) -> None:
    body = _parse_body(body_json)
    client = get_client()
    _run_write(lambda: client.build_update_watch(uuid, body, timeout=APP_STATE["timeout"]), lambda timeout: client.update_watch(uuid, body, timeout=timeout), dry_run=dry_run, pretty=pretty)


@app.command("delete_watch")
def delete_watch(
    uuid: str,
    dry_run: bool = typer.Option(False, "--dry-run", help="Print the request JSON and do not call the API."),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output"),
) -> None:
    client = get_client()
    _run_write(lambda: client.build_delete_watch(uuid, timeout=APP_STATE["timeout"]), lambda timeout: client.delete_watch(uuid, timeout=timeout), dry_run=dry_run, pretty=pretty)


@app.command("get_watch_history")
def get_watch_history(uuid: str, pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output")) -> None:
    _run(lambda timeout: get_client().get_watch_history(uuid, timeout=timeout), pretty=pretty)


@app.command("get_watch_snapshot")
def get_watch_snapshot(
    uuid: str,
    timestamp: str,
    html: bool = typer.Option(False, "--html", help="Set to 1 to return HTML."),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output"),
) -> None:
    _run(lambda timeout: get_client().get_watch_snapshot(uuid, timestamp, html=html, timeout=timeout), pretty=pretty)


@app.command("get_watch_history_diff")
def get_watch_history_diff(
    uuid: str,
    from_timestamp: str,
    to_timestamp: str,
    output_format: str | None = typer.Option(None, "--format", help="Diff output format."),
    word_diff: str | None = typer.Option(None, "--word-diff", help="One of true,false,1,0,yes,no,on,off."),
    no_markup: str | None = typer.Option(None, "--no-markup", help="One of true,false,1,0,yes,no,on,off."),
    diff_type: str | None = typer.Option(None, "--diff-type", help="One of diffLines or diffWords."),
    changes_only: str | None = typer.Option(None, "--changes-only", help="One of true,false,1,0,yes,no,on,off."),
    ignore_whitespace: str | None = typer.Option(None, "--ignore-whitespace", help="One of true,false,1,0,yes,no,on,off."),
    removed: str | None = typer.Option(None, "--removed", help="One of true,false,1,0,yes,no,on,off."),
    added: str | None = typer.Option(None, "--added", help="One of true,false,1,0,yes,no,on,off."),
    replaced: str | None = typer.Option(None, "--replaced", help="One of true,false,1,0,yes,no,on,off."),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output"),
) -> None:
    _run(
        lambda timeout: get_client().get_watch_history_diff(
            uuid,
            from_timestamp,
            to_timestamp,
            output_format=output_format,
            word_diff=word_diff,
            no_markup=no_markup,
            diff_type=diff_type,
            changes_only=changes_only,
            ignore_whitespace=ignore_whitespace,
            removed=removed,
            added=added,
            replaced=replaced,
            timeout=timeout,
        ),
        pretty=pretty,
    )


@app.command("get_watch_favicon")
def get_watch_favicon(uuid: str, pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output")) -> None:
    _run(lambda timeout: get_client().get_watch_favicon(uuid, timeout=timeout), pretty=pretty)


@app.command("list_tags")
def list_tags(pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output")) -> None:
    _run(lambda timeout: get_client().list_tags(timeout=timeout), pretty=pretty)


@app.command("create_tag")
def create_tag(
    body_json: str = typer.Option(..., "--body-json", help="JSON request body matching the upstream CreateTag schema."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Print the request JSON and do not call the API."),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output"),
) -> None:
    body = _parse_body(body_json)
    client = get_client()
    _run_write(lambda: client.build_create_tag(body, timeout=APP_STATE["timeout"]), lambda timeout: client.create_tag(body, timeout=timeout), dry_run=dry_run, pretty=pretty)


@app.command("get_tag")
def get_tag(
    uuid: str,
    muted_state: str | None = typer.Option(None, "--muted-state", help="Set mute state: muted or unmuted."),
    recheck: bool = typer.Option(False, "--recheck", help="Queue all watches in this tag for recheck."),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output"),
) -> None:
    _run(lambda timeout: get_client().get_tag(uuid, muted=muted_state, recheck=recheck, timeout=timeout), pretty=pretty)


@app.command("update_tag")
def update_tag(
    uuid: str,
    body_json: str = typer.Option(..., "--body-json", help="JSON request body matching the upstream Tag schema."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Print the request JSON and do not call the API."),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output"),
) -> None:
    body = _parse_body(body_json)
    client = get_client()
    _run_write(lambda: client.build_update_tag(uuid, body, timeout=APP_STATE["timeout"]), lambda timeout: client.update_tag(uuid, body, timeout=timeout), dry_run=dry_run, pretty=pretty)


@app.command("delete_tag")
def delete_tag(
    uuid: str,
    dry_run: bool = typer.Option(False, "--dry-run", help="Print the request JSON and do not call the API."),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output"),
) -> None:
    client = get_client()
    _run_write(lambda: client.build_delete_tag(uuid, timeout=APP_STATE["timeout"]), lambda timeout: client.delete_tag(uuid, timeout=timeout), dry_run=dry_run, pretty=pretty)


@app.command("get_notifications")
def get_notifications(pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output")) -> None:
    _run(lambda timeout: get_client().get_notifications(timeout=timeout), pretty=pretty)


@app.command("add_notifications")
def add_notifications(
    body_json: str = typer.Option(..., "--body-json", help="JSON body with notification_urls."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Print the request JSON and do not call the API."),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output"),
) -> None:
    body = _parse_body(body_json)
    client = get_client()
    _run_write(lambda: client.build_add_notifications(body, timeout=APP_STATE["timeout"]), lambda timeout: client.add_notifications(body, timeout=timeout), dry_run=dry_run, pretty=pretty)


@app.command("replace_notifications")
def replace_notifications(
    body_json: str = typer.Option(..., "--body-json", help="JSON body with notification_urls."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Print the request JSON and do not call the API."),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output"),
) -> None:
    body = _parse_body(body_json)
    client = get_client()
    _run_write(lambda: client.build_replace_notifications(body, timeout=APP_STATE["timeout"]), lambda timeout: client.replace_notifications(body, timeout=timeout), dry_run=dry_run, pretty=pretty)


@app.command("delete_notifications")
def delete_notifications(
    body_json: str = typer.Option(..., "--body-json", help="JSON body with notification_urls to delete."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Print the request JSON and do not call the API."),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output"),
) -> None:
    body = _parse_body(body_json)
    client = get_client()
    _run_write(lambda: client.build_delete_notifications(body, timeout=APP_STATE["timeout"]), lambda timeout: client.delete_notifications(body, timeout=timeout), dry_run=dry_run, pretty=pretty)


@app.command("search_watches")
def search_watches(
    query: str = typer.Option(..., "--query", help="Search query to match against watch URLs and titles."),
    tag: str | None = typer.Option(None, "--tag", help="Tag name to limit results."),
    partial: str | None = typer.Option(None, "--partial", help="Enable partial matching."),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output"),
) -> None:
    _run(lambda timeout: get_client().search_watches(query, tag=tag, partial=partial, timeout=timeout), pretty=pretty)


@app.command("import_watches")
def import_watches(
    urls: list[str] = typer.Argument(..., help="One or more URLs to import."),
    param: list[str] = typer.Option([], "--param", help="Repeat key=value query parameters for additional watch config."),
    tag_uuids: str | None = typer.Option(None, "--tag-uuids", help="Tag UUIDs to apply to imported watches."),
    tag: str | None = typer.Option(None, "--tag", help="Tag name to apply to imported watches."),
    proxy: str | None = typer.Option(None, "--proxy", help="Proxy key for imported watches."),
    dedupe: bool | None = typer.Option(None, "--dedupe/--no-dedupe", help="Skip duplicate URLs."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Print the request JSON and do not call the API."),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output"),
) -> None:
    params = _parse_query_params(param) or {}
    for key, value in {"tag_uuids": tag_uuids, "tag": tag, "proxy": proxy, "dedupe": str(dedupe).lower() if dedupe is not None else None}.items():
        if value is not None:
            params[key] = value
    client = get_client()
    _run_write(lambda: client.build_import_watches(urls, params=params or None, timeout=APP_STATE["timeout"]), lambda timeout: client.import_watches(urls, params=params or None, timeout=timeout), dry_run=dry_run, pretty=pretty)


@app.command("get_system_info")
def get_system_info(pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output")) -> None:
    _run(lambda timeout: get_client().get_system_info(timeout=timeout), pretty=pretty)


@app.command("get_full_api_spec")
def get_full_api_spec(pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output")) -> None:
    _run(lambda timeout: get_client(require_api_key=False).get_full_api_spec(timeout=timeout), pretty=pretty)


def main() -> None:
    run_app(app)


if __name__ == "__main__":
    main()
