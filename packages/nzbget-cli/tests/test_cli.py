from __future__ import annotations

from typer.testing import CliRunner

from ghostship_nzbget import cli


runner = CliRunner()


class DummyClient:
    def __init__(self):
        self.calls = []

    def get_version(self, *, timeout=None):
        self.calls.append(('get_version', timeout))
        return '1.0'

    def build_shutdown(self):
        class _Spec:
            def to_dict(self): return {'json_body': {'method': 'shutdown'}}
        return _Spec()

    def shutdown(self, *, timeout=None):
        self.calls.append(('shutdown', timeout))
        return True


def test_timeout_applies(monkeypatch):
    client = DummyClient()
    monkeypatch.setattr(cli, 'get_client', lambda: client)
    result = runner.invoke(cli.app, ['--timeout', '8', 'get_version'])
    assert result.exit_code == 0
    assert client.calls[-1] == ('get_version', 8.0)


def test_shutdown_dry_run(monkeypatch):
    client = DummyClient()
    monkeypatch.setattr(cli, 'get_client', lambda: client)
    result = runner.invoke(cli.app, ['shutdown', '--dry-run'])
    assert result.exit_code == 0
    assert 'shutdown' in result.stdout
    assert not client.calls
