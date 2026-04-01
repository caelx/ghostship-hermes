from __future__ import annotations

from ghostship_cloakbrowser.client import CloakBrowserClient


class DummyCloakBrowserClient(CloakBrowserClient):
    def __init__(self) -> None:
        super().__init__("https://cloak.example", token="secret")
        self.calls: list[tuple[str, str, dict[str, object]]] = []

    def request(self, method: str, path: str, *, params=None, json_data=None):
        self.calls.append((method, path, {"params": params, "json_data": json_data}))
        return {"ok": True}


def test_wrappers_delegate_to_request() -> None:
    client = DummyCloakBrowserClient()
    client.get_auth_status()
    client.login("secret")
    client.logout()
    client.get_system_status()
    client.list_profiles()
    client.get_profile("profile-1")
    client.create_profile("name", humanize=True)
    client.update_profile("profile-1", notes="updated")
    client.delete_profile("profile-1")
    client.launch_profile("profile-1")
    client.stop_profile("profile-1")
    client.get_profile_status("profile-1")
    client.get_clipboard("profile-1")
    client.set_clipboard("profile-1", "hello")
    client.get_cdp_info("profile-1")

    assert client.calls == [
        ("GET", "/api/auth/status", {"params": None, "json_data": None}),
        ("POST", "/api/auth/login", {"params": None, "json_data": {"token": "secret"}}),
        ("POST", "/api/auth/logout", {"params": None, "json_data": None}),
        ("GET", "/api/status", {"params": None, "json_data": None}),
        ("GET", "/api/profiles", {"params": None, "json_data": None}),
        ("GET", "/api/profiles/profile-1", {"params": None, "json_data": None}),
        ("POST", "/api/profiles", {"params": None, "json_data": {"name": "name", "platform": "windows", "screen_width": 1920, "screen_height": 1080, "humanize": True, "human_preset": "default", "headless": False, "geoip": False, "clipboard_sync": True}}),
        ("PUT", "/api/profiles/profile-1", {"params": None, "json_data": {"notes": "updated"}}),
        ("DELETE", "/api/profiles/profile-1", {"params": None, "json_data": None}),
        ("POST", "/api/profiles/profile-1/launch", {"params": None, "json_data": None}),
        ("POST", "/api/profiles/profile-1/stop", {"params": None, "json_data": None}),
        ("GET", "/api/profiles/profile-1/status", {"params": None, "json_data": None}),
        ("GET", "/api/profiles/profile-1/clipboard", {"params": None, "json_data": None}),
        ("POST", "/api/profiles/profile-1/clipboard", {"params": None, "json_data": {"text": "hello"}}),
        ("GET", "/api/profiles/profile-1/cdp", {"params": None, "json_data": None}),
    ]
