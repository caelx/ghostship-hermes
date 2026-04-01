from __future__ import annotations

from ghostship_pyload_ng.client import PyLoadClient


class DummyPyLoadClient(PyLoadClient):
    def __init__(self) -> None:
        super().__init__('https://pyload.example')
        self.calls = []

    def request(self, method: str, path: str, *, params=None, json_data=None, timeout=None):
        self.calls.append((method, path, {'params': params, 'json_data': json_data, 'timeout': timeout}))
        return {'ok': True}


def test_wrappers_delegate_to_request() -> None:
    client = DummyPyLoadClient()
    client.get_server_status(timeout=1)
    client.add_package('demo', ['https://example.com'], timeout=2)
    client.remove_account('plugin', 'login', timeout=3)
    assert client.calls == [
        ('GET', 'api/status_server', {'params': None, 'json_data': None, 'timeout': 1}),
        ('POST', '/api/add_package', {'params': None, 'json_data': {'name': 'demo', 'links': ['https://example.com']}, 'timeout': 2}),
        ('POST', '/api/remove_account', {'params': None, 'json_data': {'plugin': 'plugin', 'login': 'login'}, 'timeout': 3}),
    ]
