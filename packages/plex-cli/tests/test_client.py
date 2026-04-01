from __future__ import annotations

from ghostship_plex.client import PlexClient


class DummyPlexClient(PlexClient):
    def __init__(self) -> None:
        super().__init__('https://plex.example', 'token')
        self.calls: list[tuple[str, str, dict[str, object]]] = []

    def request(self, method: str, path: str, *, params=None, json_data=None, timeout=None):
        self.calls.append((method, path, {'params': params, 'json_data': json_data, 'timeout': timeout}))
        return {'ok': True}


def test_wrappers_delegate_to_request() -> None:
    client = DummyPlexClient()
    client.get_identity(timeout=1)
    client.get_server_info(timeout=2)
    client.refresh_library(section_id=3, timeout=4)
    client.terminate_session(9, timeout=5)
    assert client.calls == [
        ('GET', 'identity', {'params': None, 'json_data': None, 'timeout': 1}),
        ('GET', '', {'params': None, 'json_data': None, 'timeout': 2}),
        ('GET', '/library/sections/3/refresh', {'params': None, 'json_data': None, 'timeout': 4}),
        ('PUT', '/library/terminate/9', {'params': None, 'json_data': None, 'timeout': 5}),
    ]


def test_builders() -> None:
    client = PlexClient('https://plex.example', 'token')
    assert client.build_refresh_library(2).to_dict()['path'] == '/library/sections/2/refresh'
    assert client.build_terminate_session(9).to_dict()['method'] == 'PUT'
