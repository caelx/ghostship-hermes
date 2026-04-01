from __future__ import annotations

from typing import Any
import os

import httpx


def _cloudflare_access_headers() -> dict[str, str]:
    headers: dict[str, str] = {}
    client_id = os.getenv("GHOSTSHIP_TEST_CF_ACCESS_CLIENT_ID")
    client_secret = os.getenv("GHOSTSHIP_TEST_CF_ACCESS_CLIENT_SECRET")
    if client_id:
        headers["CF-Access-Client-Id"] = client_id
    if client_secret:
        headers["CF-Access-Client-Secret"] = client_secret
    return headers


class CloakBrowserClient:
    def __init__(self, base_url: str, token: str | None = None):
        self.base_url = base_url.rstrip("/")
        self.token = token
        self.headers = _cloudflare_access_headers()
        if token:
            self.headers["Authorization"] = f"Bearer {token}"

    def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json_data: dict[str, Any] | list[Any] | None = None,
    ) -> Any:
        url = f"{self.base_url}/{path.lstrip('/')}"
        with httpx.Client(headers=self.headers) as client:
            response = client.request(method.upper(), url, params=params, json=json_data)
            response.raise_for_status()
            if not response.content:
                return {"status": "success"}
            return response.json()

    def get_auth_status(self) -> dict[str, Any]:
        return self.request("GET", "/api/auth/status")

    def login(self, token: str) -> dict[str, Any]:
        return self.request("POST", "/api/auth/login", json_data={"token": token})

    def logout(self) -> dict[str, Any]:
        return self.request("POST", "/api/auth/logout")

    def get_system_status(self) -> dict[str, Any]:
        return self.request("GET", "/api/status")

    def list_profiles(self) -> list[dict[str, Any]]:
        return self.request("GET", "/api/profiles")

    def get_profile(self, profile_id: str) -> dict[str, Any]:
        return self.request("GET", f"/api/profiles/{profile_id}")

    def create_profile(
        self,
        name: str,
        fingerprint_seed: int | None = None,
        proxy: str | None = None,
        timezone: str | None = None,
        locale: str | None = None,
        platform: str = "windows",
        user_agent: str | None = None,
        screen_width: int = 1920,
        screen_height: int = 1080,
        gpu_vendor: str | None = None,
        gpu_renderer: str | None = None,
        hardware_concurrency: int | None = None,
        humanize: bool = False,
        human_preset: str = "default",
        headless: bool = False,
        geoip: bool = False,
        clipboard_sync: bool = True,
        color_scheme: str | None = None,
        notes: str | None = None,
        tags: list[dict[str, str]] | None = None,
    ) -> dict[str, Any]:
        data: dict[str, Any] = {
            "name": name,
            "platform": platform,
            "screen_width": screen_width,
            "screen_height": screen_height,
            "humanize": humanize,
            "human_preset": human_preset,
            "headless": headless,
            "geoip": geoip,
            "clipboard_sync": clipboard_sync,
        }
        optional_values = {
            "fingerprint_seed": fingerprint_seed,
            "proxy": proxy,
            "timezone": timezone,
            "locale": locale,
            "user_agent": user_agent,
            "gpu_vendor": gpu_vendor,
            "gpu_renderer": gpu_renderer,
            "hardware_concurrency": hardware_concurrency,
            "color_scheme": color_scheme,
            "notes": notes,
            "tags": tags,
        }
        data.update({key: value for key, value in optional_values.items() if value is not None})
        return self.request("POST", "/api/profiles", json_data=data)

    def update_profile(
        self,
        profile_id: str,
        name: str | None = None,
        fingerprint_seed: int | None = None,
        proxy: str | None = None,
        timezone: str | None = None,
        locale: str | None = None,
        platform: str | None = None,
        user_agent: str | None = None,
        screen_width: int | None = None,
        screen_height: int | None = None,
        gpu_vendor: str | None = None,
        gpu_renderer: str | None = None,
        hardware_concurrency: int | None = None,
        humanize: bool | None = None,
        human_preset: str | None = None,
        headless: bool | None = None,
        geoip: bool | None = None,
        clipboard_sync: bool | None = None,
        color_scheme: str | None = None,
        notes: str | None = None,
        tags: list[dict[str, str]] | None = None,
    ) -> dict[str, Any]:
        data = {
            key: value
            for key, value in {
                "name": name,
                "fingerprint_seed": fingerprint_seed,
                "proxy": proxy,
                "timezone": timezone,
                "locale": locale,
                "platform": platform,
                "user_agent": user_agent,
                "screen_width": screen_width,
                "screen_height": screen_height,
                "gpu_vendor": gpu_vendor,
                "gpu_renderer": gpu_renderer,
                "hardware_concurrency": hardware_concurrency,
                "humanize": humanize,
                "human_preset": human_preset,
                "headless": headless,
                "geoip": geoip,
                "clipboard_sync": clipboard_sync,
                "color_scheme": color_scheme,
                "notes": notes,
                "tags": tags,
            }.items()
            if value is not None
        }
        return self.request("PUT", f"/api/profiles/{profile_id}", json_data=data)

    def delete_profile(self, profile_id: str) -> Any:
        return self.request("DELETE", f"/api/profiles/{profile_id}")

    def launch_profile(self, profile_id: str) -> dict[str, Any]:
        return self.request("POST", f"/api/profiles/{profile_id}/launch")

    def stop_profile(self, profile_id: str) -> Any:
        return self.request("POST", f"/api/profiles/{profile_id}/stop")

    def get_profile_status(self, profile_id: str) -> dict[str, Any]:
        return self.request("GET", f"/api/profiles/{profile_id}/status")

    def get_clipboard(self, profile_id: str) -> dict[str, Any]:
        return self.request("GET", f"/api/profiles/{profile_id}/clipboard")

    def set_clipboard(self, profile_id: str, text: str) -> Any:
        return self.request("POST", f"/api/profiles/{profile_id}/clipboard", json_data={"text": text})

    def get_cdp_info(self, profile_id: str) -> dict[str, Any]:
        return self.request("GET", f"/api/profiles/{profile_id}/cdp")
