from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Final

MUTATING_METHODS: Final[tuple[str, ...]] = ('POST', 'PUT', 'PATCH', 'DELETE')

@dataclass(frozen=True, slots=True)
class OperationDef:
    operation_id: str
    command_name: str
    method: str
    path: str
    summary: str
    tag: str
    path_params: tuple[str, ...]
    query_params: tuple[str, ...]
    has_body: bool


def _snake_case(value: str) -> str:
    cleaned = re.sub(r"[^0-9A-Za-z]+", '_', value)
    cleaned = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', cleaned)
    cleaned = re.sub(r'_+', '_', cleaned)
    return cleaned.strip('_').lower()


def _load_operations() -> tuple[OperationDef, ...]:
    path = Path(__file__).with_name('chaptarr-openapi.json')
    spec = json.loads(path.read_text())
    operations: list[OperationDef] = []
    seen: set[str] = set()

    def _next_command_name(base: str) -> str:
        candidate = _snake_case(base)
        if not candidate:
            candidate = 'operation'
        original = candidate
        suffix = 1
        while candidate in seen:
            suffix += 1
            candidate = f"{original}_{suffix}"
        seen.add(candidate)
        return candidate

    for path_value, methods in sorted(spec.get('paths', {}).items()):
        for method, metadata in sorted(methods.items()):
            method_upper = method.upper()
            tags = metadata.get('tags') or ['General']
            tag = tags[0]
            summary = metadata.get('summary') or metadata.get('description') or ''
            summary = summary.strip().split('\n', 1)[0]
            path_params = tuple(re.findall(r'{([^}]+)}', path_value))
            query_params = tuple(
                param['name']
                for param in metadata.get('parameters', [])
                if param.get('in') == 'query' and 'name' in param
            )
            has_body = bool(metadata.get('requestBody'))
            operation_id = metadata.get('operationId') or f"{method_upper}_{path_value}"
            command_name = _next_command_name(operation_id)
            operations.append(
                OperationDef(
                    operation_id=operation_id,
                    command_name=command_name,
                    method=method_upper,
                    path=path_value,
                    summary=summary,
                    tag=tag,
                    path_params=path_params,
                    query_params=query_params,
                    has_body=has_body,
                )
            )
    return tuple(operations)


OPERATIONS: Final[tuple[OperationDef, ...]] = _load_operations()
OPERATIONS_BY_COMMAND: Final[dict[str, OperationDef]] = {op.command_name: op for op in OPERATIONS}
