from ghostship_rss_bridge.client import RssBridgeClient


class DummyResponse:
    def __init__(self, *, payload=None, text='', headers=None):
        self._payload = payload
        self.text = text
        self.headers = headers or {'content-type': 'application/json'}

    def raise_for_status(self):
        return None

    def json(self):
        if self._payload is None:
            raise AssertionError('json() should not be called')
        return self._payload


class DummyClient:
    last_request = None

    def __init__(self, *, headers=None, timeout=None, follow_redirects=None):
        self.headers = headers or {}

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def get(self, url, params=None):
        DummyClient.last_request = {'url': url, 'params': params}
        action = (params or {}).get('action')
        if action == 'findfeed':
            return DummyResponse(payload=[{'url': './?action=display&bridge=InstagramBridge&format=Atom&u=nasa', 'bridgeParams': {'bridge': 'InstagramBridge', 'u': 'nasa', 'format': 'Atom'}, 'bridgeData': {}, 'bridgeMeta': {}}])
        return DummyResponse(payload={'bridges': {}, 'total': 0})


def test_build_display_url_merges_context_and_global_params():
    client = RssBridgeClient('https://rss-bridge.example')
    url = client.build_display_url(
        bridge='InstagramBridge',
        format='Atom',
        context='Username',
        parameters={'u': 'nasa', 'media_type': 'video'},
    )

    assert url == 'https://rss-bridge.example/?action=display&bridge=InstagramBridge&context=Username&format=Atom&media_type=video&u=nasa'


def test_list_bridges_uses_list_action(monkeypatch):
    monkeypatch.setattr('ghostship_rss_bridge.client.httpx.Client', DummyClient)

    client = RssBridgeClient('https://rss-bridge.example')
    client.list_bridges()

    assert DummyClient.last_request['params'] == {'action': 'list'}


def test_find_feed_uses_findfeed_action(monkeypatch):
    monkeypatch.setattr('ghostship_rss_bridge.client.httpx.Client', DummyClient)

    client = RssBridgeClient('https://rss-bridge.example')
    client.find_feed('https://www.instagram.com/nasa/', format='Atom')

    assert DummyClient.last_request['params'] == {
        'action': 'findfeed',
        'url': 'https://www.instagram.com/nasa/',
        'format': 'Atom',
    }



def test_list_bridges_parses_legacy_list_parameter_shape(monkeypatch):
    class LegacyListClient(DummyClient):
        def get(self, url, params=None):
            DummyClient.last_request = {'url': url, 'params': params}
            return DummyResponse(
                payload={
                    'bridges': {
                        'ABCNewsBridge': {
                            'status': 'active',
                            'parameters': [
                                {
                                    'topic': {
                                        'name': 'Region',
                                        'type': 'list',
                                        'values': {'NSW': 'nsw'},
                                    }
                                }
                            ],
                        }
                    },
                    'total': 1,
                }
            )

    monkeypatch.setattr('ghostship_rss_bridge.client.httpx.Client', LegacyListClient)

    client = RssBridgeClient('https://rss-bridge.example')
    payload = client.list_bridges()

    assert 'ABCNewsBridge' in payload.bridges
    bridge = payload.bridges['ABCNewsBridge']
    assert 'global' in bridge.parameters
    assert bridge.parameters['global']['topic'].name == 'Region'
    assert bridge.parameters['global']['topic'].values == {'NSW': 'nsw'}
