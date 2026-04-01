from __future__ import annotations

from ghostship_nzbget.client import NZBGetClient


class DummyNZBGetClient(NZBGetClient):
    def __init__(self) -> None:
        super().__init__('https://nzbget.example')
        self.calls = []

    def call(self, method: str, params=None, timeout=None):
        self.calls.append((method, params, timeout))
        return True


def test_wrappers_delegate_to_call() -> None:
    client = DummyNZBGetClient()
    client.get_version(timeout=1)
    client.append_url('https://example.com', timeout=2)
    client.save_config([{'Name': 'A', 'Value': 'B'}], timeout=3)
    assert client.calls == [
        ('version', None, 1),
        ('append', ['https://example.com', '', '', 0, False, False, '', 0, 'SCORE'], 2),
        ('saveconfig', [[{'Name': 'A', 'Value': 'B'}]], 3),
    ]
