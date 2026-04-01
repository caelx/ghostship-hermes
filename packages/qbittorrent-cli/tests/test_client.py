from __future__ import annotations

from ghostship_qbittorrent.client import QBitClient


class DummyQBitClient(QBitClient):
    def __init__(self) -> None:
        super().__init__("https://qbit.example")
        self.calls: list[tuple[str, str, dict[str, object]]] = []

    def request(self, method: str, path: str, *, params=None, data=None, json_data=None, files=None):
        self.calls.append((method, path, {"params": params, "data": data, "json_data": json_data, "files": files}))
        if path == "transfer/speedLimitsMode":
            return "1"
        return "Ok."


def test_wrappers_delegate_to_request() -> None:
    client = DummyQBitClient()
    client.get_app_version()
    client.get_api_version()
    client.shutdown()
    client.get_preferences()
    client.set_preferences({"save_path": "/downloads"})
    client.get_log(last_known_id=4)
    client.get_main_data(rid=5)
    client.get_transfer_info()
    client.get_speed_limits_mode()
    client.toggle_speed_limits_mode()
    client.get_torrents(filter_type="downloading", category="tv", sort="name", reverse=True)
    client.add_torrent(["magnet:?xt=1"], save_path="/downloads", category="tv")
    client.delete_torrents(["abc"], delete_files=True)
    client.pause_torrents(["abc"])
    client.resume_torrents(["abc"])
    client.search_start("ubuntu", category="all", plugins="all")
    client.search_status(7)
    client.search_results(7, limit=5, offset=1)
    client.get_rss_data(with_data=False)

    assert client.calls[0] == ("GET", "app/version", {"params": None, "data": None, "json_data": None, "files": None})
    assert client.calls[-1] == ("GET", "rss/items", {"params": {"withData": "false"}, "data": None, "json_data": None, "files": None})
    assert any(call[1] == "app/setPreferences" for call in client.calls)
    assert any(call[1] == "torrents/add" for call in client.calls)
    assert any(call[1] == "search/results" for call in client.calls)
