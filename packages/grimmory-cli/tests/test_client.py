from ghostship_grimmory.client import GrimmoryClient


class DummyResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


def test_password_auth_fetches_token(monkeypatch):
    captured = {}

    def fake_post(url, json=None, timeout=None):
        captured["url"] = url
        captured["json"] = json
        return DummyResponse({"accessToken": "grimmory-access-token"})

    monkeypatch.setattr("ghostship_grimmory.client.httpx.post", fake_post)

    client = GrimmoryClient(
        "http://grimmory.local", username="alice", password="secret"
    )

    assert client.headers["Authorization"] == "Bearer grimmory-access-token"
    assert captured["url"] == "http://grimmory.local/api/v1/auth/login"
    assert captured["json"] == {"username": "alice", "password": "secret"}
