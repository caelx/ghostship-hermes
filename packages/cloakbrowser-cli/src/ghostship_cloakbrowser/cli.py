import json
import os
from typing import Any, Optional

import typer

from .client import CloakBrowserClient

HELP_TEXT = """CloakBrowser Manager CLI.

Auth:
- Set CLOAKBROWSER_URL to the manager base URL.
- If the manager was started with AUTH_TOKEN=..., set CLOAKBROWSER_TOKEN to that same static secret.
- There is no username/password token minting flow for API clients. If manager auth is disabled, omit CLOAKBROWSER_TOKEN.
- /api/status stays unauthenticated upstream and can be used as a health check.
"""

app = typer.Typer(help=HELP_TEXT, no_args_is_help=True)


def echo_json(data: Any, pretty: bool = False) -> None:
    indent = 2 if pretty else None
    typer.echo(json.dumps(data, indent=indent))


def get_client() -> CloakBrowserClient:
    base_url = os.getenv("CLOAKBROWSER_URL", "http://localhost:8080")
    token = os.getenv("CLOAKBROWSER_TOKEN")
    return CloakBrowserClient(base_url, token)


@app.command()
def status(
    pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output"),
) -> None:
    """Get system status information."""
    client = get_client()
    try:
        data = client.get_system_status()
        echo_json(data, pretty=pretty)
    except Exception as e:
        echo_json({"error": str(e)}, pretty=pretty)
        raise typer.Exit(code=1)


@app.command("auth-status")
def auth_status(
    pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output"),
) -> None:
    """Report whether manager auth is enabled and whether this client is authenticated."""
    client = get_client()
    try:
        data = client.get_auth_status()
        echo_json(data, pretty=pretty)
    except Exception as e:
        echo_json({"error": str(e)}, pretty=pretty)
        raise typer.Exit(code=1)


@app.command("list")
def list_profiles(
    pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output"),
) -> None:
    """List all profiles with their status and CDP URLs."""
    client = get_client()
    try:
        profiles = client.list_profiles()
        echo_json(profiles, pretty=pretty)
    except Exception as e:
        echo_json({"error": str(e)}, pretty=pretty)
        raise typer.Exit(code=1)


@app.command()
def get(
    profile_id: str,
    pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output"),
) -> None:
    """Get detailed information for a specific profile."""
    client = get_client()
    try:
        data = client.get_profile(profile_id)
        echo_json(data, pretty=pretty)
    except Exception as e:
        echo_json({"error": str(e)}, pretty=pretty)
        raise typer.Exit(code=1)


@app.command()
def create(
    name: str,
    fingerprint_seed: Optional[int] = typer.Option(None, "--fingerprint-seed"),
    proxy: Optional[str] = typer.Option(None, "--proxy"),
    timezone: Optional[str] = typer.Option(None, "--timezone"),
    locale: Optional[str] = typer.Option(None, "--locale"),
    platform: str = typer.Option("windows", "--platform"),
    user_agent: Optional[str] = typer.Option(None, "--user-agent"),
    screen_width: int = typer.Option(1920, "--screen-width"),
    screen_height: int = typer.Option(1080, "--screen-height"),
    gpu_vendor: Optional[str] = typer.Option(None, "--gpu-vendor"),
    gpu_renderer: Optional[str] = typer.Option(None, "--gpu-renderer"),
    hardware_concurrency: Optional[int] = typer.Option(None, "--hardware-concurrency"),
    humanize: bool = typer.Option(False, "--humanize"),
    human_preset: str = typer.Option("default", "--human-preset"),
    headless: bool = typer.Option(False, "--headless"),
    geoip: bool = typer.Option(False, "--geoip"),
    clipboard_sync: bool = typer.Option(True, "--clipboard-sync/--no-clipboard-sync"),
    color_scheme: Optional[str] = typer.Option(None, "--color-scheme"),
    notes: Optional[str] = typer.Option(None, "--notes"),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output"),
) -> None:
    """Create a new browser profile."""
    client = get_client()
    try:
        data = client.create_profile(
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
        )
        echo_json(data, pretty=pretty)
    except Exception as e:
        echo_json({"error": str(e)}, pretty=pretty)
        raise typer.Exit(code=1)


@app.command()
def update(
    profile_id: str,
    name: Optional[str] = typer.Option(None, "--name"),
    fingerprint_seed: Optional[int] = typer.Option(None, "--fingerprint-seed"),
    proxy: Optional[str] = typer.Option(None, "--proxy"),
    timezone: Optional[str] = typer.Option(None, "--timezone"),
    locale: Optional[str] = typer.Option(None, "--locale"),
    platform: Optional[str] = typer.Option(None, "--platform"),
    user_agent: Optional[str] = typer.Option(None, "--user-agent"),
    screen_width: Optional[int] = typer.Option(None, "--screen-width"),
    screen_height: Optional[int] = typer.Option(None, "--screen-height"),
    gpu_vendor: Optional[str] = typer.Option(None, "--gpu-vendor"),
    gpu_renderer: Optional[str] = typer.Option(None, "--gpu-renderer"),
    hardware_concurrency: Optional[int] = typer.Option(None, "--hardware-concurrency"),
    humanize: Optional[bool] = typer.Option(None, "--humanize/--no-humanize"),
    human_preset: Optional[str] = typer.Option(None, "--human-preset"),
    headless: Optional[bool] = typer.Option(None, "--headless/--no-headless"),
    geoip: Optional[bool] = typer.Option(None, "--geoip/--no-geoip"),
    clipboard_sync: Optional[bool] = typer.Option(
        None, "--clipboard-sync/--no-clipboard-sync"
    ),
    color_scheme: Optional[str] = typer.Option(None, "--color-scheme"),
    notes: Optional[str] = typer.Option(None, "--notes"),
    pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output"),
) -> None:
    """Update an existing browser profile."""
    client = get_client()
    try:
        data = client.update_profile(
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
        )
        echo_json(data, pretty=pretty)
    except Exception as e:
        echo_json({"error": str(e)}, pretty=pretty)
        raise typer.Exit(code=1)


@app.command()
def delete(
    profile_id: str,
    pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output"),
) -> None:
    """Delete a browser profile."""
    client = get_client()
    try:
        result = client.delete_profile(profile_id)
        echo_json({"ok": result}, pretty=pretty)
    except Exception as e:
        echo_json({"error": str(e)}, pretty=pretty)
        raise typer.Exit(code=1)


@app.command()
def launch(
    profile_id: str,
    pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output"),
) -> None:
    """Launch a browser profile."""
    client = get_client()
    try:
        data = client.launch_profile(profile_id)
        echo_json(data, pretty=pretty)
    except Exception as e:
        echo_json({"error": str(e)}, pretty=pretty)
        raise typer.Exit(code=1)


@app.command()
def stop(
    profile_id: str,
    pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output"),
) -> None:
    """Stop a running browser profile."""
    client = get_client()
    try:
        result = client.stop_profile(profile_id)
        echo_json({"ok": result}, pretty=pretty)
    except Exception as e:
        echo_json({"error": str(e)}, pretty=pretty)
        raise typer.Exit(code=1)


@app.command()
def profile_status(
    profile_id: str,
    pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output"),
) -> None:
    """Get status of a specific profile."""
    client = get_client()
    try:
        data = client.get_profile_status(profile_id)
        echo_json(data, pretty=pretty)
    except Exception as e:
        echo_json({"error": str(e)}, pretty=pretty)
        raise typer.Exit(code=1)


@app.command()
def clipboard_get(
    profile_id: str,
    pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output"),
) -> None:
    """Get clipboard text from a running profile."""
    client = get_client()
    try:
        data = client.get_clipboard(profile_id)
        echo_json(data, pretty=pretty)
    except Exception as e:
        echo_json({"error": str(e)}, pretty=pretty)
        raise typer.Exit(code=1)


@app.command()
def clipboard_set(
    profile_id: str,
    text: str,
    pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output"),
) -> None:
    """Set clipboard text in a running profile."""
    client = get_client()
    try:
        result = client.set_clipboard(profile_id, text)
        echo_json({"ok": result}, pretty=pretty)
    except Exception as e:
        echo_json({"error": str(e)}, pretty=pretty)
        raise typer.Exit(code=1)


@app.command()
def cdp_info(
    profile_id: str,
    pretty: bool = typer.Option(False, "--pretty", help="Pretty print JSON output"),
) -> None:
    """Get CDP connection info for a profile."""
    client = get_client()
    try:
        data = client.get_cdp_info(profile_id)
        echo_json(data, pretty=pretty)
    except Exception as e:
        echo_json({"error": str(e)}, pretty=pretty)
        raise typer.Exit(code=1)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
