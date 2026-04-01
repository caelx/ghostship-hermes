import json

from typer.testing import CliRunner

from ghostship_pricebuddy import cli


runner = CliRunner()


class DummyClient:
    def __init__(self):
        self.calls = []

    def get_current_user(self, *, timeout=None):
        self.calls.append(('get_current_user', timeout))
        return {'id': 1, 'name': 'Alice', 'email': 'alice@example.com'}

    def build_create_product(self, request, *, timeout=None):
        class _Spec:
            def __init__(self, payload):
                self.payload = payload
            def to_dict(self):
                return self.payload
        return _Spec({'method': 'POST', 'path': '/api/products', 'json_body': request.to_payload(), 'timeout': timeout})

    def create_product(self, request, *, timeout=None):
        self.calls.append(('create_product', request.title, timeout))
        return {'data': {'id': 7, 'title': request.title}}

    def search_all_product_sources(self, query, *, timeout=None):
        self.calls.append(('search_all_product_sources', query, timeout))
        return [{'title': 'Laptop Deal', 'url': 'https://store.example/laptop', 'source': 'Deals'}]


def test_timeout_applies(monkeypatch):
    client = DummyClient()
    monkeypatch.setattr(cli, 'get_client', lambda: client)
    result = runner.invoke(cli.app, ['--timeout', '8', 'get_current_user'])
    assert result.exit_code == 0
    assert client.calls[-1] == ('get_current_user', 8.0)


def test_create_product_dry_run(monkeypatch):
    client = DummyClient()
    monkeypatch.setattr(cli, 'get_client', lambda: client)
    result = runner.invoke(cli.app, ['create_product', '--title', 'Steam Deck', '--url', 'https://store.example/steam-deck', '--notify-price', '399.99', '--favourite', '--dry-run'])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload['path'] == '/api/products'
    assert payload['json_body']['title'] == 'Steam Deck'
    assert payload['json_body']['notify_price'] == '399.99'
    assert not client.calls


def test_search_all_product_sources_outputs_json(monkeypatch):
    client = DummyClient()
    monkeypatch.setattr(cli, 'get_client', lambda: client)
    result = runner.invoke(cli.app, ['search_all_product_sources', 'laptop'])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload[0]['title'] == 'Laptop Deal'
