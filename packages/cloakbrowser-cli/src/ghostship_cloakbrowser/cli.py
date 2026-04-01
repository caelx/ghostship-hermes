from __future__ import annotations

import os
from typing import Any

import typer

from ghostship_cli_contract import DEFAULT_TIMEOUT, echo_json, parse_json_option, parse_params, run_app, run_cli_command

from .client import CloakBrowserClient

HELP_TEXT = """CloakBrowser Manager CLI.

Auth:
- Set CLOAKBROWSER_URL to the manager base URL.
- If the manager was started with AUTH_TOKEN=..., set CLOAKBROWSER_TOKEN to that same static secret.
- There is no username/password token minting flow for API clients. If manager auth is disabled, omit CLOAKBROWSER_TOKEN.
- Canonical command names mirror the API/client operation names exactly.
"""

app = typer.Typer(help=HELP_TEXT, no_args_is_help=True)
APP_STATE = {'timeout': DEFAULT_TIMEOUT}


@app.callback()
def app_callback(timeout: float = typer.Option(DEFAULT_TIMEOUT, '--timeout', help='Hard timeout in seconds for all API calls in this invocation.')) -> None:
    APP_STATE['timeout'] = timeout


def get_client() -> CloakBrowserClient:
    base_url = os.getenv('CLOAKBROWSER_URL', 'http://localhost:8080')
    token = os.getenv('CLOAKBROWSER_TOKEN')
    return CloakBrowserClient(base_url, token, default_timeout=APP_STATE['timeout'])


def _emit(data: Any, pretty: bool) -> None:
    echo_json(data, pretty=pretty)


def _run(execute, *, pretty: bool) -> None:
    _emit(run_cli_command(None, execute, timeout=APP_STATE['timeout']), pretty)


def _run_write(build_request, execute, *, dry_run: bool, pretty: bool) -> None:
    _emit(run_cli_command(build_request, execute, timeout=APP_STATE['timeout'], dry_run=dry_run), pretty)


@app.command('request')
def request(method: str, path: str, param: list[str] = typer.Option([], '--param', help='Repeat key=value query parameters.'), body_json: str | None = typer.Option(None, '--body-json', help='Optional JSON request body.'), dry_run: bool = typer.Option(False, '--dry-run', help='Print the request JSON and do not call the API.'), pretty: bool = typer.Option(False, '--pretty', help='Pretty print JSON output')) -> None:
    client = get_client()
    params = parse_params(param) or None
    payload = parse_json_option(body_json, '--body-json')
    _run_write(lambda: client.build_request(method, path, params=params, json_data=payload), lambda timeout: client.request(method, path, params=params, json_data=payload, timeout=timeout), dry_run=dry_run, pretty=pretty)


@app.command('get_system_status')
def get_system_status(pretty: bool = typer.Option(False, '--pretty', help='Pretty print JSON output')) -> None:
    client = get_client()
    _run(lambda timeout: client.get_system_status(timeout=timeout), pretty=pretty)


@app.command('auth_status')
def auth_status(pretty: bool = typer.Option(False, '--pretty', help='Pretty print JSON output')) -> None:
    client = get_client()
    _run(lambda timeout: client.get_auth_status(timeout=timeout), pretty=pretty)


@app.command('auth_login')
def auth_login(token: str, dry_run: bool = typer.Option(False, '--dry-run', help='Print the request JSON and do not call the API.'), pretty: bool = typer.Option(False, '--pretty', help='Pretty print JSON output')) -> None:
    client = get_client()
    _run_write(lambda: client.build_request('POST', '/api/auth/login', json_data={'token': token}), lambda timeout: client.auth_login(token, timeout=timeout), dry_run=dry_run, pretty=pretty)


@app.command('auth_logout')
def auth_logout(dry_run: bool = typer.Option(False, '--dry-run', help='Print the request JSON and do not call the API.'), pretty: bool = typer.Option(False, '--pretty', help='Pretty print JSON output')) -> None:
    client = get_client()
    _run_write(lambda: client.build_request('POST', '/api/auth/logout'), lambda timeout: client.auth_logout(timeout=timeout), dry_run=dry_run, pretty=pretty)


@app.command('list_profiles')
def list_profiles(pretty: bool = typer.Option(False, '--pretty', help='Pretty print JSON output')) -> None:
    client = get_client()
    _run(lambda timeout: client.list_profiles(timeout=timeout), pretty=pretty)


@app.command('get_profile')
def get_profile(profile_id: str, pretty: bool = typer.Option(False, '--pretty', help='Pretty print JSON output')) -> None:
    client = get_client()
    _run(lambda timeout: client.get_profile(profile_id, timeout=timeout), pretty=pretty)


@app.command('create_profile')
def create_profile(
    name: str,
    fingerprint_seed: int | None = typer.Option(None, '--fingerprint-seed'),
    proxy: str | None = typer.Option(None, '--proxy'),
    timezone: str | None = typer.Option(None, '--timezone'),
    locale: str | None = typer.Option(None, '--locale'),
    platform: str = typer.Option('windows', '--platform'),
    user_agent: str | None = typer.Option(None, '--user-agent'),
    screen_width: int = typer.Option(1920, '--screen-width'),
    screen_height: int = typer.Option(1080, '--screen-height'),
    gpu_vendor: str | None = typer.Option(None, '--gpu-vendor'),
    gpu_renderer: str | None = typer.Option(None, '--gpu-renderer'),
    hardware_concurrency: int | None = typer.Option(None, '--hardware-concurrency'),
    humanize: bool = typer.Option(False, '--humanize'),
    human_preset: str = typer.Option('default', '--human-preset'),
    headless: bool = typer.Option(False, '--headless'),
    geoip: bool = typer.Option(False, '--geoip'),
    clipboard_sync: bool = typer.Option(True, '--clipboard-sync/--no-clipboard-sync'),
    color_scheme: str | None = typer.Option(None, '--color-scheme'),
    notes: str | None = typer.Option(None, '--notes'),
    dry_run: bool = typer.Option(False, '--dry-run', help='Print the request JSON and do not call the API.'),
    pretty: bool = typer.Option(False, '--pretty', help='Pretty print JSON output'),
) -> None:
    client = get_client()
    kwargs = {
        'name': name,
        'fingerprint_seed': fingerprint_seed,
        'proxy': proxy,
        'timezone': timezone,
        'locale': locale,
        'platform': platform,
        'user_agent': user_agent,
        'screen_width': screen_width,
        'screen_height': screen_height,
        'gpu_vendor': gpu_vendor,
        'gpu_renderer': gpu_renderer,
        'hardware_concurrency': hardware_concurrency,
        'humanize': humanize,
        'human_preset': human_preset,
        'headless': headless,
        'geoip': geoip,
        'clipboard_sync': clipboard_sync,
        'color_scheme': color_scheme,
        'notes': notes,
    }
    _run_write(lambda: client.build_create_profile(**kwargs), lambda timeout: client.create_profile(timeout=timeout, **kwargs), dry_run=dry_run, pretty=pretty)


@app.command('update_profile')
def update_profile(
    profile_id: str,
    name: str | None = typer.Option(None, '--name'),
    fingerprint_seed: int | None = typer.Option(None, '--fingerprint-seed'),
    proxy: str | None = typer.Option(None, '--proxy'),
    timezone: str | None = typer.Option(None, '--timezone'),
    locale: str | None = typer.Option(None, '--locale'),
    platform: str | None = typer.Option(None, '--platform'),
    user_agent: str | None = typer.Option(None, '--user-agent'),
    screen_width: int | None = typer.Option(None, '--screen-width'),
    screen_height: int | None = typer.Option(None, '--screen-height'),
    gpu_vendor: str | None = typer.Option(None, '--gpu-vendor'),
    gpu_renderer: str | None = typer.Option(None, '--gpu-renderer'),
    hardware_concurrency: int | None = typer.Option(None, '--hardware-concurrency'),
    humanize: bool | None = typer.Option(None, '--humanize/--no-humanize'),
    human_preset: str | None = typer.Option(None, '--human-preset'),
    headless: bool | None = typer.Option(None, '--headless/--no-headless'),
    geoip: bool | None = typer.Option(None, '--geoip/--no-geoip'),
    clipboard_sync: bool | None = typer.Option(None, '--clipboard-sync/--no-clipboard-sync'),
    color_scheme: str | None = typer.Option(None, '--color-scheme'),
    notes: str | None = typer.Option(None, '--notes'),
    dry_run: bool = typer.Option(False, '--dry-run', help='Print the request JSON and do not call the API.'),
    pretty: bool = typer.Option(False, '--pretty', help='Pretty print JSON output'),
) -> None:
    client = get_client()
    kwargs = {
        'name': name,
        'fingerprint_seed': fingerprint_seed,
        'proxy': proxy,
        'timezone': timezone,
        'locale': locale,
        'platform': platform,
        'user_agent': user_agent,
        'screen_width': screen_width,
        'screen_height': screen_height,
        'gpu_vendor': gpu_vendor,
        'gpu_renderer': gpu_renderer,
        'hardware_concurrency': hardware_concurrency,
        'humanize': humanize,
        'human_preset': human_preset,
        'headless': headless,
        'geoip': geoip,
        'clipboard_sync': clipboard_sync,
        'color_scheme': color_scheme,
        'notes': notes,
    }
    _run_write(lambda: client.build_update_profile(profile_id, **kwargs), lambda timeout: client.update_profile(profile_id, timeout=timeout, **kwargs), dry_run=dry_run, pretty=pretty)


@app.command('delete_profile')
def delete_profile(profile_id: str, dry_run: bool = typer.Option(False, '--dry-run', help='Print the request JSON and do not call the API.'), pretty: bool = typer.Option(False, '--pretty', help='Pretty print JSON output')) -> None:
    client = get_client()
    _run_write(lambda: client.build_delete_profile(profile_id), lambda timeout: client.delete_profile(profile_id, timeout=timeout), dry_run=dry_run, pretty=pretty)


@app.command('launch_profile')
def launch_profile(profile_id: str, dry_run: bool = typer.Option(False, '--dry-run', help='Print the request JSON and do not call the API.'), pretty: bool = typer.Option(False, '--pretty', help='Pretty print JSON output')) -> None:
    client = get_client()
    _run_write(lambda: client.build_launch_profile(profile_id), lambda timeout: client.launch_profile(profile_id, timeout=timeout), dry_run=dry_run, pretty=pretty)


@app.command('stop_profile')
def stop_profile(profile_id: str, dry_run: bool = typer.Option(False, '--dry-run', help='Print the request JSON and do not call the API.'), pretty: bool = typer.Option(False, '--pretty', help='Pretty print JSON output')) -> None:
    client = get_client()
    _run_write(lambda: client.build_stop_profile(profile_id), lambda timeout: client.stop_profile(profile_id, timeout=timeout), dry_run=dry_run, pretty=pretty)


@app.command('get_profile_status')
def get_profile_status(profile_id: str, pretty: bool = typer.Option(False, '--pretty', help='Pretty print JSON output')) -> None:
    client = get_client()
    _run(lambda timeout: client.get_profile_status(profile_id, timeout=timeout), pretty=pretty)


@app.command('get_clipboard')
def get_clipboard(profile_id: str, pretty: bool = typer.Option(False, '--pretty', help='Pretty print JSON output')) -> None:
    client = get_client()
    _run(lambda timeout: client.get_clipboard(profile_id, timeout=timeout), pretty=pretty)


@app.command('set_clipboard')
def set_clipboard(profile_id: str, text: str, dry_run: bool = typer.Option(False, '--dry-run', help='Print the request JSON and do not call the API.'), pretty: bool = typer.Option(False, '--pretty', help='Pretty print JSON output')) -> None:
    client = get_client()
    _run_write(lambda: client.build_set_clipboard(profile_id, text), lambda timeout: client.set_clipboard(profile_id, text, timeout=timeout), dry_run=dry_run, pretty=pretty)


@app.command('get_cdp_info')
def get_cdp_info(profile_id: str, pretty: bool = typer.Option(False, '--pretty', help='Pretty print JSON output')) -> None:
    client = get_client()
    _run(lambda timeout: client.get_cdp_info(profile_id, timeout=timeout), pretty=pretty)


def main() -> None:
    run_app(app)


if __name__ == '__main__':
    main()
