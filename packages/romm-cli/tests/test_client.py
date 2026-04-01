from __future__ import annotations

from ghostship_romm.client import RommClient


class DummyRommClient(RommClient):
    def __init__(self) -> None:
        super().__init__('https://romm.example', token='secret')
        self.calls = []

    def request(self, method: str, path: str, *, params=None, json_data=None, timeout=None):
        self.calls.append((method, path, {'params': params, 'json_data': json_data, 'timeout': timeout}))
        return {'ok': True}


def test_wrappers_delegate_to_request() -> None:
    client = DummyRommClient()
    client.get_heartbeat(timeout=1)
    client.update_rom(5, {'title': 'demo'}, timeout=2)
    client.start_scan(timeout=3)
    assert client.calls == [
        ('GET', 'heartbeat', {'params': None, 'json_data': None, 'timeout': 1}),
        ('PUT', '/roms/5', {'params': None, 'json_data': {'title': 'demo'}, 'timeout': 2}),
        ('POST', '/scans', {'params': None, 'json_data': None, 'timeout': 3}),
    ]
