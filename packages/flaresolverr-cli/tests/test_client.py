from __future__ import annotations

from ghostship_flaresolverr.client import FlareSolverrClient


class DummyFlareSolverrClient(FlareSolverrClient):
    def __init__(self) -> None:
        super().__init__('https://flaresolverr.example')
        self.calls: list[tuple[str, dict[str, object], float | None]] = []

    def command(self, cmd: str, timeout: float | None = None, **kwargs):
        self.calls.append((cmd, kwargs, timeout))
        return {'ok': True}


def test_wrappers_delegate_to_command() -> None:
    client = DummyFlareSolverrClient()
    client.request_get('https://example.com', session='a', timeout=1)
    client.request_post('https://example.com', 'body', session='b', timeout=2)
    client.sessions_create(session='c', timeout=3)
    client.sessions_list(timeout=4)
    client.sessions_destroy('d', timeout=5)

    assert client.calls == [
        ('request.get', {'url': 'https://example.com', 'session': 'a'}, 1),
        ('request.post', {'url': 'https://example.com', 'postData': 'body', 'session': 'b'}, 2),
        ('sessions.create', {'session': 'c'}, 3),
        ('sessions.list', {}, 4),
        ('sessions.destroy', {'session': 'd'}, 5),
    ]


def test_request_builders() -> None:
    client = FlareSolverrClient('https://flaresolverr.example')
    assert client.build_command('sessions.list').to_dict()['json_body']['cmd'] == 'sessions.list'
    assert client.build_request_post('https://example.com', 'body').to_dict()['json_body']['postData'] == 'body'
