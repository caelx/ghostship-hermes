from __future__ import annotations

from ghostship_flaresolverr.client import FlareSolverrClient


class DummyFlareSolverrClient(FlareSolverrClient):
    def __init__(self) -> None:
        super().__init__("https://flaresolverr.example")
        self.calls: list[tuple[str, dict[str, object]]] = []

    def command(self, cmd: str, **kwargs):
        self.calls.append((cmd, kwargs))
        return {"ok": True}


def test_wrappers_delegate_to_command() -> None:
    client = DummyFlareSolverrClient()
    client.request_get("https://example.com", session="a")
    client.request_post("https://example.com", "body", session="b")
    client.sessions_create(session="c")
    client.sessions_list()
    client.sessions_destroy("d")

    assert client.calls == [
        ("request.get", {"url": "https://example.com", "session": "a"}),
        ("request.post", {"url": "https://example.com", "postData": "body", "session": "b"}),
        ("sessions.create", {"session": "c"}),
        ("sessions.list", {}),
        ("sessions.destroy", {"session": "d"}),
    ]
