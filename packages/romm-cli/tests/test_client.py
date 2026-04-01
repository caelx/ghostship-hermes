from __future__ import annotations

from ghostship_romm.client import RommClient


class DummyRommClient(RommClient):
    def __init__(self) -> None:
        super().__init__("https://romm.example", token="token")
        self.calls: list[tuple[str, str, dict[str, object]]] = []

    def request(self, method: str, path: str, *, params=None, json_data=None):
        self.calls.append((method, path, {"params": params, "json_data": json_data}))
        return {"ok": True}


def test_wrappers_delegate_to_request() -> None:
    client = DummyRommClient()
    client.get_heartbeat()
    client.get_platforms()
    client.get_libraries()
    client.get_roms(page=2, page_size=5, platform="snes")
    client.get_rom(3)
    client.update_rom(3, {"name": "Test"})
    client.delete_rom(3)
    client.get_scans()
    client.start_scan()
    client.start_scan(4)
    client.get_collections()
    client.get_config()
    client.get_saves(page=2, page_size=5)
    client.get_saves_summary()
    client.get_save(6)
    client.get_users()
    client.get_user_me()

    assert client.calls[0] == ("GET", "heartbeat", {"params": None, "json_data": None})
    assert client.calls[-1] == ("GET", "users/me", {"params": None, "json_data": None})
    assert any(call[1] == "roms" for call in client.calls)
    assert any(call[1] == "scans/4" for call in client.calls)
