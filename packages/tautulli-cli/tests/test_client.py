from __future__ import annotations

from ghostship_tautulli.client import TautulliClient


class DummyTautulliClient(TautulliClient):
    def __init__(self) -> None:
        super().__init__("https://tautulli.example", "token")
        self.calls: list[tuple[str, dict[str, object]]] = []

    def call(self, cmd: str, **kwargs):
        self.calls.append((cmd, kwargs))
        return {"ok": True}


def test_wrappers_delegate_to_call() -> None:
    client = DummyTautulliClient()
    client.get_server_status()
    client.get_tautulli_info()
    client.get_status()
    client.get_activity()
    client.terminate_session("abc", message="bye")
    client.get_history(page=2, length=5, search="office")
    client.get_libraries()
    client.get_library_user_stats(4)
    client.get_users()
    client.get_user_player_stats(7)
    client.get_user_watch_time_stats(7)
    client.get_metadata(9)
    client.search("office", limit=3)
    client.restart()

    assert client.calls == [
        ("server_status", {}),
        ("get_tautulli_info", {}),
        ("status", {}),
        ("get_activity", {}),
        ("terminate_session", {"session_id": "abc", "message": "bye"}),
        ("get_history", {"start": 5, "length": 5, "order_column": "date", "order_dir": "desc", "search": "office"}),
        ("get_libraries", {}),
        ("get_library_user_stats", {"section_id": 4}),
        ("get_users", {}),
        ("get_user_player_stats", {"user_id": 7}),
        ("get_user_watch_time_stats", {"user_id": 7}),
        ("get_metadata", {"rating_key": 9}),
        ("search", {"query": "office", "limit": 3}),
        ("restart", {}),
    ]
