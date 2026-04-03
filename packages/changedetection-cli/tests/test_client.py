from __future__ import annotations

import base64

import httpx

from ghostship_changedetection.client import ChangedetectionClient


def test_changedetection_client_uses_expected_routes() -> None:
    seen: list[tuple[str, str, str | None, str | None]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append((request.method, request.url.path, request.url.query.decode() or None, request.headers.get("x-api-key")))
        if request.url.path.endswith("/full-spec"):
            return httpx.Response(200, text="openapi: 3.1.0", headers={"content-type": "application/yaml"})
        if request.url.path.endswith("/favicon"):
            return httpx.Response(200, content=b"ico", headers={"content-type": "image/x-icon"})
        return httpx.Response(200, json={"ok": True})

    client = ChangedetectionClient("https://changedetection.example", "secret-token", default_timeout=30.0)
    client.transport = httpx.MockTransport(handler)

    assert client.list_watches(tag="production") == {"ok": True}
    assert client.get_full_api_spec()["body"] == "openapi: 3.1.0"
    favicon = client.get_watch_favicon("watch-1")
    assert favicon["body_base64"] == base64.b64encode(b"ico").decode("ascii")
    assert seen == [
        ("GET", "/api/v1/watch", "tag=production", "secret-token"),
        ("GET", "/api/v1/full-spec", None, "secret-token"),
        ("GET", "/api/v1/watch/watch-1/favicon", None, "secret-token"),
    ]


def test_changedetection_builders() -> None:
    client = ChangedetectionClient("https://changedetection.example", "secret-token")

    create_watch_spec = client.build_create_watch({"url": "https://example.com"})
    assert create_watch_spec.to_dict()["path"] == "/watch"

    import_spec = client.build_import_watches(["https://example.com", "https://example.org"], params={"tag": "production"})
    assert import_spec.to_dict()["path"] == "/import"
    assert import_spec.to_dict()["content"] == "https://example.com\nhttps://example.org"
    assert import_spec.to_dict()["params"] == {"tag": "production"}

    delete_tag_spec = client.build_delete_tag("tag-1")
    assert delete_tag_spec.to_dict()["path"] == "/tag/tag-1"
