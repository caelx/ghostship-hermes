from __future__ import annotations

from typer.testing import CliRunner

from ghostship_grimmory import cli


runner = CliRunner()


class DummyClient:
    def __init__(self):
        self.calls = []

    def get_books(self, *, page=0, size=20, library_id=None, timeout=None):
        self.calls.append(('get_books', timeout))
        return {'ok': True}

    def build_scan_libraries(self):
        class _Spec:
            def to_dict(self): return {'path': '/libraries/scan'}
        return _Spec()

    def scan_libraries(self, *, timeout=None):
        self.calls.append(('scan_libraries', timeout))
        return {'ok': True}


def test_timeout_applies(monkeypatch):
    client = DummyClient()
    monkeypatch.setattr(cli, 'get_client', lambda: client)
    result = runner.invoke(cli.app, ['--timeout', '8', 'get_books'])
    assert result.exit_code == 0
    assert client.calls[-1] == ('get_books', 8.0)


def test_scan_libraries_dry_run(monkeypatch):
    client = DummyClient()
    monkeypatch.setattr(cli, 'get_client', lambda: client)
    result = runner.invoke(cli.app, ['scan_libraries', '--dry-run'])
    assert result.exit_code == 0
    assert '/libraries/scan' in result.stdout
    assert not client.calls
