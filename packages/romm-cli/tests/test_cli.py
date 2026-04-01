from __future__ import annotations

from typer.testing import CliRunner

from ghostship_romm import cli


runner = CliRunner()


class DummyClient:
    def __init__(self):
        self.calls = []

    def get_heartbeat(self, *, timeout=None):
        self.calls.append(('get_heartbeat', timeout))
        return {'ok': True}

    def build_update_rom(self, rom_id, data):
        class _Spec:
            def __init__(self, payload): self.payload = payload
            def to_dict(self): return self.payload
        return _Spec({'path': f'/roms/{rom_id}', 'json_body': data})

    def update_rom(self, rom_id, data, *, timeout=None):
        self.calls.append(('update_rom', rom_id, data, timeout))
        return {'ok': True}


def test_timeout_applies(monkeypatch):
    client = DummyClient()
    monkeypatch.setattr(cli, 'get_client', lambda: client)
    result = runner.invoke(cli.app, ['--timeout', '8', 'get_heartbeat'])
    assert result.exit_code == 0
    assert client.calls[-1] == ('get_heartbeat', 8.0)


def test_update_rom_dry_run(monkeypatch):
    client = DummyClient()
    monkeypatch.setattr(cli, 'get_client', lambda: client)
    result = runner.invoke(cli.app, ['update_rom', '5', '--body-json', '{"title":"demo"}', '--dry-run'])
    assert result.exit_code == 0
    assert '/roms/5' in result.stdout
    assert not client.calls
