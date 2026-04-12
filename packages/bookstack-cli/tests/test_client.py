from __future__ import annotations

from pathlib import Path

import httpx

from ghostship_bookstack.client import BookStackClient


def test_bookstack_client_uses_expected_routes() -> None:
    seen: list[tuple[str, str, str | None, str | None, str | None]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append((
            request.method,
            request.url.path,
            request.url.query.decode() or None,
            request.headers.get('Authorization'),
            request.headers.get('content-type'),
        ))
        if request.url.path.endswith('/export/markdown'):
            return httpx.Response(200, request=request, content=b'# Page', headers={'content-type': 'text/markdown'})
        return httpx.Response(200, request=request, json={'ok': True})

    client = BookStackClient('https://bookstack.example', 'token-id', 'token-secret', default_timeout=30.0, transport=httpx.MockTransport(handler))

    assert client.pages_list(query_params={'count': '5'}) == {'ok': True}
    response = client.pages_export_markdown(path_params={'id': '42'})
    assert response.content == b'# Page'
    assert seen == [
        ('GET', '/api/pages', 'count=5', 'Token token-id:token-secret', None),
        ('GET', '/api/pages/42/export/markdown', None, 'Token token-id:token-secret', None),
    ]


def test_bookstack_multipart_put_uses_method_override(tmp_path: Path) -> None:
    seen: list[tuple[str, str, bytes]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append((request.method, request.url.path, request.content))
        return httpx.Response(200, request=request, json={'ok': True})

    payload = tmp_path / 'cover.png'
    payload.write_bytes(b'png')

    client = BookStackClient('https://bookstack.example', 'token-id', 'token-secret', transport=httpx.MockTransport(handler))
    client.books_update(path_params={'id': '7'}, form_data={'name': 'Updated'}, files={'image': (payload.name, payload.read_bytes(), 'image/png')})

    method, path, content = seen[0]
    assert method == 'POST'
    assert path == '/api/books/7'
    assert b'name' in content
    assert b'Updated' in content
    assert b'_method' in content
    assert b'PUT' in content


def test_bookstack_builders_validate_path_params() -> None:
    client = BookStackClient('https://bookstack.example', 'token-id', 'token-secret')

    spec = client.build_pages_read(path_params={'id': 'page-1'})
    assert spec.to_dict()['path'] == '/pages/page-1'

    dry_run_spec = client.build_attachments_create(form_data={'name': 'guide.pdf', 'uploaded_to': '123'})
    assert dry_run_spec.to_dict()['path'] == '/attachments'
    assert dry_run_spec.to_dict()['form_data'] == {'name': 'guide.pdf', 'uploaded_to': '123'}
