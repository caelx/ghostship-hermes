import json

from typer.testing import CliRunner

from ghostship_rss_bridge.cli import app


runner = CliRunner()


def test_build_url_returns_json_wrapper(monkeypatch):
    class DummyClient:
        def build_display_url(self, *, bridge, format, context, parameters):
            assert bridge == 'InstagramBridge'
            assert format == 'Atom'
            assert context == 'Username'
            assert parameters == {'u': 'nasa'}
            return 'https://rss-bridge.example/?action=display&bridge=InstagramBridge&context=Username&format=Atom&u=nasa'

    monkeypatch.setattr('ghostship_rss_bridge.cli.get_client', lambda: DummyClient())

    result = runner.invoke(
        app,
        ['build-url', '--bridge', 'InstagramBridge', '--format', 'Atom', '--context', 'Username', '--param', 'u=nasa'],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload['url'].startswith('https://rss-bridge.example/')


def test_find_feed_returns_candidates(monkeypatch):
    class DummyClient:
        def find_feed(self, url, format):
            return [
                {
                    'url': 'https://rss-bridge.example/?action=display&bridge=InstagramBridge&context=Username&format=Atom&u=nasa',
                    'bridgeParams': {'bridge': 'InstagramBridge', 'context': 'Username', 'u': 'nasa', 'format': 'Atom'},
                }
            ]

    monkeypatch.setattr('ghostship_rss_bridge.cli.get_client', lambda: DummyClient())

    result = runner.invoke(app, ['find-feed', 'https://www.instagram.com/nasa/', '--format', 'Atom'])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload[0]['bridgeParams']['bridge'] == 'InstagramBridge'


def test_bridge_describe_returns_single_bridge(monkeypatch):
    class DummyClient:
        def get_bridge(self, bridge):
            assert bridge == 'RedditBridge'
            return {'status': 'active', 'name': 'Reddit Bridge', 'parameters': {'global': {}}}

    monkeypatch.setattr('ghostship_rss_bridge.cli.get_client', lambda: DummyClient())

    result = runner.invoke(app, ['describe-bridge', 'RedditBridge'])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload['name'] == 'Reddit Bridge'
