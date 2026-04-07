from __future__ import annotations

import httpx

from ghostship_n8n.client import N8nClient


def test_n8n_client_uses_expected_routes() -> None:
    seen: list[tuple[str, str, str | None, str | None]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(
            (
                request.method,
                request.url.path,
                request.url.query.decode() or None,
                request.headers.get('X-N8N-API-KEY'),
            )
        )
        return httpx.Response(200, json={'ok': True})

    client = N8nClient('https://n8n.example', 'secret-token', default_timeout=30.0)
    client.transport = httpx.MockTransport(handler)

    assert client.get_workflows(query_params={'active': 'true'}) == {'ok': True}
    assert client.get_workflow(path_params={'id': 'wf-1'}) == {'ok': True}
    assert client.update_execution_tags(
        path_params={'id': '42'},
        json_body={'tagIds': ['tag-1']},
    ) == {'ok': True}
    assert seen == [
        ('GET', '/api/v1/workflows', 'active=true', 'secret-token'),
        ('GET', '/api/v1/workflows/wf-1', None, 'secret-token'),
        ('PUT', '/api/v1/executions/42/tags', None, 'secret-token'),
    ]


def test_n8n_builders_validate_path_params() -> None:
    client = N8nClient('https://n8n.example', 'secret-token')

    spec = client.build_get_workflow(path_params={'id': 'workflow-1'})
    assert spec.to_dict()['path'] == '/workflows/workflow-1'

    dry_run_spec = client.build_create_tag(json_body={'name': 'production'})
    assert dry_run_spec.to_dict()['path'] == '/tags'
    assert dry_run_spec.to_dict()['json_body'] == {'name': 'production'}
