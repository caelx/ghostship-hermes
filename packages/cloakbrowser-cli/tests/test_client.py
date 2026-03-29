from ghostship_cloakbrowser.client import CloakBrowserClient


class DummyClient:
    def __init__(self, headers=None):
        self.headers = headers or {}

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def get(self, url, params=None):
        DummyClient.last_url = url
        return DummyResponse({"ok": True})


class DummyResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


def test_request_urls_include_separator(monkeypatch):
    monkeypatch.setattr("ghostship_cloakbrowser.client.httpx.Client", DummyClient)

    client = CloakBrowserClient("http://cloak.local:8080", token="secret")
    client.get_system_status()

    assert DummyClient.last_url == "http://cloak.local:8080/api/status"
