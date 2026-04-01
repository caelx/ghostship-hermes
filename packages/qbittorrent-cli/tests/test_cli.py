from __future__ import annotations

from typer.testing import CliRunner

from ghostship_qbittorrent import cli


runner = CliRunner()


class DummyClient:
    def __init__(self):
        self.calls = []

    def get_app_version(self, *, timeout=None):
        self.calls.append(('get_app_version', timeout))
        return '1.0'

    def build_add_torrent(self, urls, save_path=None, category=None):
        class _Spec:
            def __init__(self, payload): self.payload = payload
            def to_dict(self): return self.payload
        return _Spec({'form_data': {'urls': '\n'.join(urls), 'savepath': save_path, 'category': category}})

    def add_torrent(self, urls, save_path=None, category=None, *, timeout=None):
        self.calls.append(('add_torrent', urls, save_path, category, timeout))
        return True


def test_timeout_applies(monkeypatch):
    client = DummyClient()
    monkeypatch.setattr(cli, 'get_client', lambda: client)
    result = runner.invoke(cli.app, ['--timeout', '8', 'get_app_version'])
    assert result.exit_code == 0
    assert client.calls[-1] == ('get_app_version', 8.0)


def test_add_torrent_dry_run(monkeypatch):
    client = DummyClient()
    monkeypatch.setattr(cli, 'get_client', lambda: client)
    result = runner.invoke(cli.app, ['add_torrent', 'https://example.com/file.torrent', '--dry-run'])
    assert result.exit_code == 0
    assert 'file.torrent' in result.stdout
    assert not client.calls
