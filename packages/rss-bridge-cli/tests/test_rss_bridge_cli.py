from __future__ import annotations

from typer.testing import CliRunner

from ghostship_rss_bridge import cli


runner = CliRunner()


class DummyClient:
    def __init__(self):
        self.calls = []

    def list_bridges(self):
        self.calls.append(('list_bridges', {}))
        class Payload:
            bridges = {}
            total = 0
            def to_dict(self): return {'bridges': {}, 'total': 0}
        return Payload()

    def build_display_url(self, **kwargs):
        self.calls.append(('build_display_url', kwargs))
        return 'https://rss.example/feed'


def test_list_bridges(monkeypatch):
    client = DummyClient()
    monkeypatch.setattr(cli, 'get_client', lambda: client)
    result = runner.invoke(cli.app, ['list_bridges'])
    assert result.exit_code == 0
    assert client.calls[-1][0] == 'list_bridges'


def test_build_url(monkeypatch):
    client = DummyClient()
    monkeypatch.setattr(cli, 'get_client', lambda: client)
    result = runner.invoke(cli.app, ['build_url', '--bridge', 'DemoBridge', '--param', 'q=test'])
    assert result.exit_code == 0
    assert 'https://rss.example/feed' in result.stdout
