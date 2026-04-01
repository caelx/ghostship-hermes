from __future__ import annotations

from ghostship_tautulli.client import TautulliClient


class DummyTautulliClient(TautulliClient):
    def __init__(self) -> None:
        super().__init__('https://tautulli.example', 'key')
        self.calls = []

    def call(self, cmd: str, timeout: float | None = None, **kwargs):
        self.calls.append((cmd, kwargs, timeout))
        return {'ok': True}


def test_wrappers_delegate_to_call() -> None:
    client = DummyTautulliClient()
    client.get_server_status(timeout=1)
    client.terminate_session('abc', message='bye', timeout=2)
    client.restart(timeout=3)
    assert client.calls == [
        ('server_status', {}, 1),
        ('terminate_session', {'session_id': 'abc', 'message': 'bye'}, 2),
        ('restart', {}, 3),
    ]


def test_builders() -> None:
    client = TautulliClient('https://tautulli.example', 'key')
    assert client.build_call('status').to_dict()['params']['cmd'] == 'status'
    assert client.build_restart().to_dict()['params']['cmd'] == 'restart'
