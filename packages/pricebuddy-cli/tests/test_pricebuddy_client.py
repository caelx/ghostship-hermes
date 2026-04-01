from ghostship_pricebuddy.client import PriceBuddyClient


class DummyResponse:
    def __init__(self, payload):
        self._payload = payload
        self.status_code = 200
        self.content = b"{}"

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


class DummyClient:
    last_request = None

    def __init__(self, *, headers=None, timeout=None):
        self.headers = headers or {}
        self.timeout = timeout

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def request(self, method, url, params=None, json=None):
        DummyClient.last_request = {
            'method': method,
            'url': url,
            'params': params,
            'json': json,
            'headers': self.headers,
        }
        if url.endswith('/api/user'):
            return DummyResponse({'id': 1, 'name': 'Alice', 'email': 'alice@example.com'})
        return DummyResponse({'data': [], 'links': {}, 'meta': {}})


def test_pricebuddy_client_uses_bearer_token(monkeypatch):
    monkeypatch.setattr('ghostship_pricebuddy.client.httpx.Client', DummyClient)

    client = PriceBuddyClient('https://pricebuddy.example', token='secret-token')
    client.get_current_user()

    assert DummyClient.last_request['url'] == 'https://pricebuddy.example/api/user'
    assert DummyClient.last_request['headers']['Authorization'] == 'Bearer secret-token'


def test_list_products_builds_expected_query(monkeypatch):
    monkeypatch.setattr('ghostship_pricebuddy.client.httpx.Client', DummyClient)

    client = PriceBuddyClient('https://pricebuddy.example', token='secret-token')
    client.list_products(
        include=['tags', 'user'],
        sort='title',
        filters={'status': 'p', 'favourite': 'true'},
        per_page=25,
        page=2,
    )

    assert DummyClient.last_request['params'] == {
        'include': 'tags,user',
        'sort': 'title',
        'filter[status]': 'p',
        'filter[favourite]': 'true',
        'per_page': '25',
        'page': '2',
    }


def test_search_all_product_sources_uses_search_route(monkeypatch):
    monkeypatch.setattr('ghostship_pricebuddy.client.httpx.Client', DummyClient)

    client = PriceBuddyClient('https://pricebuddy.example', token='secret-token')
    client.search_all_product_sources('ssd deal')

    assert DummyClient.last_request['url'] == 'https://pricebuddy.example/api/product-sources/search/ssd%20deal'
