from __future__ import annotations

from ghostship_grimmory.client import GrimmoryClient


class DummyGrimmoryClient(GrimmoryClient):
    def __init__(self) -> None:
        super().__init__("https://grimmory.example", token="token")
        self.calls: list[tuple[str, str, dict[str, object]]] = []

    def request(self, method: str, path: str, *, params=None, json_data=None):
        self.calls.append((method, path, {"params": params, "json_data": json_data}))
        return {"ok": True}


def test_wrappers_delegate_to_request() -> None:
    client = DummyGrimmoryClient()
    client.get_books(page=1, size=5, library_id=2)
    client.get_book(3)
    client.download_book(3)
    client.get_libraries()
    client.get_library(1)
    client.scan_libraries()
    client.refresh_library(1)
    client.get_authors(page=1, size=5)
    client.get_author(2)
    client.get_shelves()
    client.get_shelf_books(4)
    client.get_tasks()
    client.cancel_task("abc")
    client.get_version()

    assert client.calls[0] == ("GET", "books", {"params": {"page": 1, "size": 5, "libraryId": 2}, "json_data": None})
    assert client.calls[-1] == ("GET", "version", {"params": None, "json_data": None})
    assert any(call[1] == "libraries/scan" for call in client.calls)
    assert any(call[1] == "tasks/abc/cancel" for call in client.calls)
