from ghostship_romm.client import RommClient


class DummyResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


def test_password_auth_fetches_token(monkeypatch):
    captured = {}

    def fake_post(url, data=None, timeout=None):
        captured["url"] = url
        captured["data"] = data
        return DummyResponse(
            {
                "access_token": "romm-access-token",
                "token_type": "bearer",
                "expires": 3600,
            }
        )

    monkeypatch.setattr("ghostship_romm.client.httpx.post", fake_post)

    client = RommClient("http://romm.local", username="alice", password="secret")

    assert client.headers["Authorization"] == "Bearer romm-access-token"
    assert captured["url"] == "http://romm.local/api/token"
    assert captured["data"]["grant_type"] == "password"
    assert captured["data"]["username"] == "alice"
    assert captured["data"]["password"] == "secret"
