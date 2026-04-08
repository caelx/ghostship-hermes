from __future__ import annotations

from typing import Any, Mapping
from urllib.parse import quote

from ghostship_cli_contract import BaseHttpClient, InvalidInputError, RequestSpec

from .catalog import OperationDef, OPERATIONS, OPERATIONS_BY_COMMAND


class ChaptarrClient(BaseHttpClient):
    SPEC_DEFAULT_API_PATH = 'api'
    SPEC_DEFAULT_API_VERSION = 'v1'

    def __init__(
        self,
        base_url: str,
        api_key: str,
        *,
        api_path: str = SPEC_DEFAULT_API_PATH,
        api_version: str = SPEC_DEFAULT_API_VERSION,
        default_timeout: float = 30.0,
    ):
        normalized_base = base_url.rstrip('/')
        normalized_path = api_path.strip('/') or self.SPEC_DEFAULT_API_PATH
        normalized_version = api_version.strip('/') or self.SPEC_DEFAULT_API_VERSION
        headers = {
            'Accept': 'application/json',
            'X-Api-Key': api_key,
        }
        super().__init__(normalized_base, default_headers=headers, default_timeout=default_timeout)
        prefix_parts: list[str] = []
        if normalized_path:
            prefix_parts.append(normalized_path)
        if normalized_version:
            prefix_parts.append(normalized_version)
        self.api_prefix = '/' + '/'.join(prefix_parts) if prefix_parts else ''
        self.spec_prefix = f"/{self.SPEC_DEFAULT_API_PATH}/{self.SPEC_DEFAULT_API_VERSION}"

    def build_request(
        self,
        method: str,
        path: str,
        *,
        query_params: Mapping[str, Any] | None = None,
        json_body: Any = None,
        timeout: float | None = None,
    ) -> RequestSpec:
        return self.build_request_spec(
            method,
            path,
            params=dict(query_params) if query_params is not None else None,
            json_body=json_body,
            timeout=timeout,
        )

    def normalize_path(self, path: str) -> str:
        return self._apply_api_prefix(path)

    def _apply_api_prefix(self, rendered_path: str) -> str:
        path = rendered_path if rendered_path.startswith('/') else f'/{rendered_path}'
        if path.startswith(self.spec_prefix):
            path = path[len(self.spec_prefix):] or '/'
        if not path.startswith('/'):
            path = f'/{path}'
        if path == '/':
            return self.api_prefix
        return f"{self.api_prefix.rstrip('/')}{path}"

    def _render_path(self, operation: OperationDef, path_params: Mapping[str, Any] | None) -> str:
        params = dict(path_params or {})
        missing = [name for name in operation.path_params if name not in params]
        if missing:
            joined = ', '.join(missing)
            raise InvalidInputError(f"missing required path parameters for {operation.command_name}: {joined}")

        rendered = operation.path
        for name in operation.path_params:
            rendered = rendered.replace('{' + name + '}', quote(str(params[name]), safe=''))

        unexpected = sorted(set(params) - set(operation.path_params))
        if unexpected:
            joined = ', '.join(unexpected)
            raise InvalidInputError(f"unexpected path parameters for {operation.command_name}: {joined}")
        return self._apply_api_prefix(rendered)

    def build_operation_request(
        self,
        command_name: str,
        *,
        path_params: Mapping[str, Any] | None = None,
        query_params: Mapping[str, Any] | None = None,
        json_body: Any = None,
        timeout: float | None = None,
    ) -> RequestSpec:
        operation = OPERATIONS_BY_COMMAND[command_name]
        if json_body is not None and not operation.has_body:
            raise InvalidInputError(f"{command_name} does not accept a JSON request body")
        return self.build_request(
            operation.method,
            self._render_path(operation, path_params),
            query_params=query_params,
            json_body=json_body,
            timeout=timeout,
        )

    def request_operation(
        self,
        command_name: str,
        *,
        path_params: Mapping[str, Any] | None = None,
        query_params: Mapping[str, Any] | None = None,
        json_body: Any = None,
        timeout: float | None = None,
    ) -> Any:
        operation = OPERATIONS_BY_COMMAND[command_name]
        if json_body is not None and not operation.has_body:
            raise InvalidInputError(f"{command_name} does not accept a JSON request body")
        return self.request_json(
            operation.method,
            self._render_path(operation, path_params),
            params=dict(query_params) if query_params is not None else None,
            json_body=json_body,
            timeout=timeout,
        )


def _make_build_method(command_name: str):
    def _method(
        self: ChaptarrClient,
        *,
        path_params: Mapping[str, Any] | None = None,
        query_params: Mapping[str, Any] | None = None,
        json_body: Any = None,
        timeout: float | None = None,
    ) -> RequestSpec:
        return self.build_operation_request(
            command_name,
            path_params=path_params,
            query_params=query_params,
            json_body=json_body,
            timeout=timeout,
        )

    _method.__name__ = f'build_{command_name}'
    return _method


def _make_call_method(command_name: str):
    def _method(
        self: ChaptarrClient,
        *,
        path_params: Mapping[str, Any] | None = None,
        query_params: Mapping[str, Any] | None = None,
        json_body: Any = None,
        timeout: float | None = None,
    ) -> Any:
        return self.request_operation(
            command_name,
            path_params=path_params,
            query_params=query_params,
            json_body=json_body,
            timeout=timeout,
        )

    _method.__name__ = command_name
    return _method


for _operation in OPERATIONS:
    setattr(
        ChaptarrClient,
        f'build_{_operation.command_name}',
        _make_build_method(_operation.command_name),
    )
    setattr(ChaptarrClient, _operation.command_name, _make_call_method(_operation.command_name))


__all__ = ['ChaptarrClient']
