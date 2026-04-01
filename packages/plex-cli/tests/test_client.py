from __future__ import annotations

from ghostship_plex.client import PlexClient


class DummyPlexClient(PlexClient):
    def __init__(self) -> None:
        super().__init__("https://plex.example", "token")
        self.calls: list[tuple[str, str, dict[str, object]]] = []

    def request(self, method: str, path: str, *, params=None, json_data=None):
        self.calls.append((method, path, {"params": params, "json_data": json_data}))
        return {"MediaContainer": {}}


def test_wrappers_delegate_to_request() -> None:
    client = DummyPlexClient()
    client.get_identity()
    client.get_server_info()
    client.get_status_sessions()
    client.get_activities()
    client.get_library_sections()
    client.get_library_section(1)
    client.get_library_filters(1)
    client.get_library_sorts(1)
    client.refresh_library()
    client.refresh_library(1)
    client.get_metadata(3)
    client.get_metadata_children(3)
    client.get_playlists()
    client.get_playlist_items(4)
    client.get_collections(1)
    client.get_preferences()
    client.get_butler_tasks()
    client.get_statistics()
    client.terminate_session(7)
    client.get_session(7)

    assert client.calls[0] == ("GET", "identity", {"params": None, "json_data": None})
    assert client.calls[-1] == ("GET", "sessions/7", {"params": None, "json_data": None})
    assert any(call[1] == "library/sections/all/refresh" for call in client.calls)
    assert any(call[1] == ":/prefs" for call in client.calls)
