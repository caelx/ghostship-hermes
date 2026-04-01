from ghostship_pricebuddy.client import PriceBuddyClient, TagCreateRequest


class DummyPriceBuddyClient(PriceBuddyClient):
    def __init__(self):
        super().__init__('https://pricebuddy.example', 'secret-token')
        self.calls = []

    def request(self, method, path, *, params=None, json_data=None, timeout=None):
        self.calls.append((method, path, params, json_data, timeout))
        if path == 'user':
            return {'id': 1, 'name': 'Alice', 'email': 'alice@example.com'}
        if path == 'products':
            return {'data': [], 'links': {}, 'meta': {}}
        if path.startswith('product-sources/search/'):
            return []
        return {'data': [], 'links': {}, 'meta': {}}


def test_pricebuddy_client_uses_expected_routes() -> None:
    client = DummyPriceBuddyClient()
    user = client.get_current_user(timeout=1)
    products = client.list_products(include=['tags', 'user'], sort='title', filters={'status': 'p', 'favourite': 'true'}, per_page=25, page=2, timeout=2)
    client.search_all_product_sources('ssd deal', timeout=3)
    assert user.email == 'alice@example.com'
    assert products.meta == {}
    assert client.calls == [
        ('GET', 'user', None, None, 1),
        ('GET', 'products', {'include': 'tags,user', 'sort': 'title', 'filter[status]': 'p', 'filter[favourite]': 'true', 'per_page': '25', 'page': '2'}, None, 2),
        ('GET', 'product-sources/search/ssd%20deal', None, None, 3),
    ]


def test_builders() -> None:
    client = PriceBuddyClient('https://pricebuddy.example', token='secret-token')
    create_spec = client.build_create_tag(TagCreateRequest(name='deal-watch'))
    assert create_spec.to_dict()['path'] == '/api/tags'
    delete_spec = client.build_delete_product(7)
    assert delete_spec.to_dict()['path'] == '/api/products/7'
