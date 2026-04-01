from __future__ import annotations

import json
import os
from typing import Any

import typer

from .client import CloakBrowserClient

HELP_TEXT = """CloakBrowser Manager CLI.

Auth:
- Set CLOAKBROWSER_URL to the manager base URL.
- If the manager was started with AUTH_TOKEN=..., set CLOAKBROWSER_TOKEN to that same static secret.
- There is no username/password token minting flow for API clients. If manager auth is disabled, omit CLOAKBROWSER_TOKEN.
- Canonical command names mirror the API/client operation names exactly.
"""

app = typer.Typer(help=HELP_TEXT, no_args_is_help=True)


def echo_json(data: Any, pretty: bool = False) -> None:
    indent = 2 if pretty else None
    typer.echo(json.dumps(data, indent=indent))


def _parse_json_option(value: str | None, option_name: str) -> Any:
    if value is None:
        return None
    try:
        return json.loads(value)
    except json.JSONDecodeError as exc:
        raise typer.BadParameter(f"{option_name} must be valid JSON: {exc}") from exc


def _parse_pairs(values: list[str]) -> dict[str, str]:
    params: dict[str, str] = {}
    for value in values:
        if "=" not in value:
            raise typer.BadParameter(f"parameter must use key=value form: {value}")
        key, raw = value.split("=", 1)
        params[key] = raw
    return params


def get_client() -> CloakBrowserClient:
    base_url = os.getenv("CLOAKBROWSER_URL", "http://localhost:8080")
    token = os.getenv("CLOAKBROWSER_TOKEN")
    return CloakBrowserClient(base_url, token)


@app.command("request")
def request(
    method: str,
    path: str,
    param: list[str] = typer.Option([], "--param", help="Repeat key=value query parameters."),
    body_json: str | None = typer.Option(None, "--body-json", help="Optional JSON request body."),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output"),
) -> None:
    """Call any CloakBrowser Manager endpoint directly."""
    echo_json(
        get_client().request(
            method,
            path,
            params=_parse_pairs(param) or None,
            json_data=_parse_json_option(body_json, "--body-json"),
        ),
        pretty=pretty,
    )


@app.command("get_system_status")
def get_system_status(pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output")) -> None:
    echo_json(get_client().get_system_status(), pretty=pretty)


@app.command("auth_status")
def auth_status(pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output")) -> None:
    echo_json(get_client().get_auth_status(), pretty=pretty)


@app.command("auth_login")
def auth_login(token: str, pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output")) -> None:
    echo_json(get_client().login(token), pretty=pretty)


@app.command("auth_logout")
def auth_logout(pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output")) -> None:
    echo_json(get_client().logout(), pretty=pretty)


@app.command("list_profiles")
def list_profiles(pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output")) -> None:
    echo_json(get_client().list_profiles(), pretty=pretty)


@app.command("get_profile")
def get_profile(profile_id: str, pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output")) -> None:
    echo_json(get_client().get_profile(profile_id), pretty=pretty)


@app.command("create_profile")
def create_profile(
    name: str,
    fingerprint_seed: int | None = typer.Option(None, "--fingerprint-seed"),
    proxy: str | None = typer.Option(None, "--proxy"),
    timezone: str | None = typer.Option(None, "--timezone"),
    locale: str | None = typer.Option(None, "--locale"),
    platform: str = typer.Option("windows", "--platform"),
    user_agent: str | None = typer.Option(None, "--user-agent"),
    screen_width: int = typer.Option(1920, "--screen-width"),
    screen_height: int = typer.Option(1080, "--screen-height"),
    gpu_vendor: str | None = typer.Option(None, "--gpu-vendor"),
    gpu_renderer: str | None = typer.Option(None, "--gpu-renderer"),
    hardware_concurrency: int | None = typer.Option(None, "--hardware-concurrency"),
    humanize: bool = typer.Option(False, "--humanize"),
    human_preset: str = typer.Option("default", "--human-preset"),
    headless: bool = typer.Option(False, "--headless"),
    geoip: bool = typer.Option(False, "--geoip"),
    clipboard_sync: bool = typer.Option(True, "--clipboard-sync/--no-clipboard-sync"),
    color_scheme: str | None = typer.Option(None, "--color-scheme"),
    notes: str | None = typer.Option(None, "--notes"),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output"),
) -> None:
    echo_json(
        get_client().create_profile(
            name=name,
            fingerprint_seed=fingerprint_seed,
            proxy=proxy,
            timezone=timezone,
            locale=locale,
            platform=platform,
            user_agent=user_agent,
            screen_width=screen_width,
            screen_height=screen_height,
            gpu_vendor=gpu_vendor,
            gpu_renderer=gpu_renderer,
            hardware_concurrency=hardware_concurrency,
            humanize=humanize,
            human_preset=human_preset,
            headless=headless,
            geoip=geoip,
            clipboard_sync=clipboard_sync,
            color_scheme=color_scheme,
            notes=notes,
        ),
        pretty=pretty,
    )


@app.command("update_profile")
def update_profile(
    profile_id: str,
    name: str | None = typer.Option(None, "--name"),
    fingerprint_seed: int | None = typer.Option(None, "--fingerprint-seed"),
    proxy: str | None = typer.Option(None, "--proxy"),
    timezone: str | None = typer.Option(None, "--timezone"),
    locale: str | None = typer.Option(None, "--locale"),
    platform: str | None = typer.Option(None, "--platform"),
    user_agent: str | None = typer.Option(None, "--user-agent"),
    screen_width: int | None = typer.Option(None, "--screen-width"),
    screen_height: int | None = typer.Option(None, "--screen-height"),
    gpu_vendor: str | None = typer.Option(None, "--gpu-vendor"),
    gpu_renderer: str | None = typer.Option(None, "--gpu-renderer"),
    hardware_concurrency: int | None = typer.Option(None, "--hardware-concurrency"),
    humanize: bool | None = typer.Option(None, "--humanize/--no-humanize"),
    human_preset: str | None = typer.Option(None, "--human-preset"),
    headless: bool | None = typer.Option(None, "--headless/--no-headless"),
    geoip: bool | None = typer.Option(None, "--geoip/--no-geoip"),
    clipboard_sync: bool | None = typer.Option(None, "--clipboard-sync/--no-clipboard-sync"),
    color_scheme: str | None = typer.Option(None, "--color-scheme"),
    notes: str | None = typer.Option(None, "--notes"),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output"),
) -> None:
    echo_json(
        get_client().update_profile(
            profile_id=profile_id,
            name=name,
            fingerprint_seed=fingerprint_seed,
            proxy=proxy,
            timezone=timezone,
            locale=locale,
            platform=platform,
            user_agent=user_agent,
            screen_width=screen_width,
            screen_height=screen_height,
            gpu_vendor=gpu_vendor,
            gpu_renderer=gpu_renderer,
            hardware_concurrency=hardware_concurrency,
            humanize=humanize,
            human_preset=human_preset,
            headless=headless,
            geoip=geoip,
            clipboard_sync=clipboard_sync,
            color_scheme=color_scheme,
            notes=notes,
        ),
        pretty=pretty,
    )


@app.command("delete_profile")
def delete_profile(profile_id: str, pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output")) -> None:
    echo_json(get_client().delete_profile(profile_id), pretty=pretty)


@app.command("launch_profile")
def launch_profile(profile_id: str, pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output")) -> None:
    echo_json(get_client().launch_profile(profile_id), pretty=pretty)


@app.command("stop_profile")
def stop_profile(profile_id: str, pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output")) -> None:
    echo_json(get_client().stop_profile(profile_id), pretty=pretty)


@app.command("get_profile_status")
def get_profile_status(profile_id: str, pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output")) -> None:
    echo_json(get_client().get_profile_status(profile_id), pretty=pretty)


@app.command("get_clipboard")
def get_clipboard(profile_id: str, pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output")) -> None:
    echo_json(get_client().get_clipboard(profile_id), pretty=pretty)


@app.command("set_clipboard")
def set_clipboard(profile_id: str, text: str, pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output")) -> None:
    echo_json(get_client().set_clipboard(profile_id, text), pretty=pretty)


@app.command("get_cdp_info")
def get_cdp_info(profile_id: str, pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output")) -> None:
    echo_json(get_client().get_cdp_info(profile_id), pretty=pretty)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
