from __future__ import annotations

from ghostship_qbittorrent.client import QBitClient


class DummyQBitClient(QBitClient):
    def __init__(self) -> None:
        super().__init__('https://qb.example')
        self.calls = []

    def request(self, method: str, path: str, *, params=None, data=None, json_data=None, timeout=None):
        self.calls.append((method, path, {'params': params, 'data': data, 'json_data': json_data, 'timeout': timeout}))
        if path == 'transfer/speedLimitsMode':
            return '1'
        return 'Ok.'


def test_wrappers_delegate_to_request() -> None:
    client = DummyQBitClient()
    client.get_app_version(timeout=1)
    client.set_preferences({'x': 1}, timeout=2)
    client.delete_torrents(['abc'], timeout=3)
    assert client.calls == [
        ('GET', 'app/version', {'params': None, 'data': None, 'json_data': None, 'timeout': 1}),
        ('POST', 'app/setPreferences', {'params': None, 'data': {'json': '{"x": 1}'}, 'json_data': None, 'timeout': 2}),
        ('POST', '/torrents/delete', {'params': None, 'data': {'hashes': 'abc', 'deleteFiles': 'false'}, 'json_data': None, 'timeout': 3}),
    ]
