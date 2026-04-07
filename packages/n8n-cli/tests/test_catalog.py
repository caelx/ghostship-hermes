from __future__ import annotations

import json
from pathlib import Path

from ghostship_n8n.catalog import OPERATIONS
from ghostship_n8n.client import N8nClient


def test_catalog_matches_openapi_snapshot() -> None:
    snapshot = json.loads(Path('docs/api/n8n-openapi.json').read_text())
    operation_ids = {
        operation['x-eov-operation-id']
        for path_item in snapshot['paths'].values()
        for operation in path_item.values()
        if isinstance(operation, dict) and 'x-eov-operation-id' in operation
    }
    assert operation_ids == {operation.operation_id for operation in OPERATIONS}


def test_client_exposes_dedicated_methods_for_every_operation() -> None:
    missing = []
    for operation in OPERATIONS:
        if not hasattr(N8nClient, operation.command_name):
            missing.append(operation.command_name)
        if not hasattr(N8nClient, f'build_{operation.command_name}'):
            missing.append(f'build_{operation.command_name}')
    assert not missing
