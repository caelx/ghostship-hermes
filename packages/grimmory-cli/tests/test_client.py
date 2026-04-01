from __future__ import annotations

from ghostship_grimmory.client import GrimmoryClient


class DummyGrimmoryClient(GrimmoryClient):
    def __init__(self) -> None:
        super().__init__('https://grimmory.example', token='secret')
        self.calls = []

    def request(self, method: str, path: str, *, params=None, json_data=None, timeout=None):
        self.calls.append((method, path, {'params': params, 'json_data': json_data, 'timeout': timeout}))
        return {'ok': True}


def test_wrappers_delegate_to_request() -> None:
    client = DummyGrimmoryClient()
    client.get_books(timeout=1)
    client.scan_libraries(timeout=2)
    client.cancel_task('t1', timeout=3)
    assert client.calls == [
        ('GET', 'books', {'params': {'page': 0, 'size': 20}, 'json_data': None, 'timeout': 1}),
        ('POST', '/libraries/scan', {'params': None, 'json_data': None, 'timeout': 2}),
        ('DELETE', '/tasks/t1/cancel', {'params': None, 'json_data': None, 'timeout': 3}),
    ]
