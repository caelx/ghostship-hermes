from __future__ import annotations

from ghostship_nzbget.client import NZBGetClient


class DummyNZBGetClient(NZBGetClient):
    def __init__(self) -> None:
        super().__init__("https://nzbget.example")
        self.calls: list[tuple[str, list[object] | None]] = []

    def call(self, method: str, params=None):
        self.calls.append((method, params))
        return True


def test_wrappers_delegate_to_call() -> None:
    client = DummyNZBGetClient()
    client.get_version()
    client.shutdown()
    client.reload()
    client.get_status()
    client.list_groups()
    client.list_files(3)
    client.get_history()
    client.append_url("http://example.com/test.nzb", category="tv", priority=100)
    client.edit_queue("GroupPause", 0, 1, [2])
    client.disk_scan()
    client.get_log(0, 10)
    client.set_rate(100)
    client.pause_download()
    client.resume_download()
    client.pause_post()
    client.resume_post()
    client.pause_scan()
    client.resume_scan()
    client.get_config()
    client.save_config([{"Name": "foo", "Value": "bar"}])

    assert client.calls == [
        ("version", None),
        ("shutdown", None),
        ("reload", None),
        ("status", None),
        ("listgroups", None),
        ("listfiles", [0, 0, 3]),
        ("history", None),
        ("append", ["http://example.com/test.nzb", "", "tv", 100, False, False, "", 0, "SCORE"]),
        ("editqueue", ["GroupPause", 0, 1, [2]]),
        ("scan", None),
        ("log", [0, 10]),
        ("rate", [100]),
        ("pausedownload", None),
        ("resumedownload", None),
        ("pausepost", None),
        ("resumepost", None),
        ("pausescan", None),
        ("resumescan", None),
        ("config", None),
        ("saveconfig", [[{"Name": "foo", "Value": "bar"}]]),
    ]
