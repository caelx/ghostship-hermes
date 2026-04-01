import json

from typer.testing import CliRunner

from ghostship_pricebuddy.cli import app


runner = CliRunner()


def test_whoami_outputs_json(monkeypatch):
    class DummyClient:
        def get_current_user(self):
            return {'id': 1, 'name': 'Alice', 'email': 'alice@example.com'}

    monkeypatch.setattr('ghostship_pricebuddy.cli.get_client', lambda: DummyClient())

    result = runner.invoke(app, ['whoami'])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload['email'] == 'alice@example.com'


def test_products_create_accepts_minimal_fields(monkeypatch):
    captured = {}

    class DummyClient:
        def create_product(self, request):
            captured['request'] = request
            return {'data': {'id': 7, 'title': request.title}}

    monkeypatch.setattr('ghostship_pricebuddy.cli.get_client', lambda: DummyClient())

    result = runner.invoke(
        app,
        [
            'products',
            'create',
            '--title',
            'Steam Deck',
            '--url',
            'https://store.example/steam-deck',
            '--notify-price',
            '399.99',
            '--favourite',
        ],
    )

    assert result.exit_code == 0
    assert captured['request'].title == 'Steam Deck'
    assert str(captured['request'].notify_price) == '399.99'
    assert captured['request'].favourite is True


def test_product_sources_search_all_returns_json(monkeypatch):
    class DummyClient:
        def search_all_product_sources(self, query):
            assert query == 'laptop'
            return [
                {'title': 'Laptop Deal', 'url': 'https://store.example/laptop', 'source': 'Deals'}
            ]

    monkeypatch.setattr('ghostship_pricebuddy.cli.get_client', lambda: DummyClient())

    result = runner.invoke(app, ['product-sources', 'search-all', 'laptop'])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload[0]['title'] == 'Laptop Deal'
