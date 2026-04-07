from __future__ import annotations

from typing import Any, Mapping
from urllib.parse import quote

from ghostship_cli_contract import BaseHttpClient, InvalidInputError, RequestSpec

from .catalog import OPERATIONS, OPERATIONS_BY_COMMAND, OperationDef


class N8nClient(BaseHttpClient):
    def __init__(
        self,
        base_url: str,
        api_key: str,
        *,
        api_path: str = 'api',
        api_version: str = 'v1',
        default_timeout: float = 30.0,
    ):
        normalized_base = base_url.rstrip('/')
        normalized_path = api_path.strip('/')
        normalized_version = api_version.strip('/')
        full_base = f"{normalized_base}/{normalized_path}/{normalized_version}"
        headers = {
            'Accept': 'application/json',
            'X-N8N-API-KEY': api_key,
        }
        super().__init__(full_base, default_headers=headers, default_timeout=default_timeout)
        self.api_path = normalized_path
        self.api_version = normalized_version

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
        return rendered

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
        self: N8nClient,
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
        self: N8nClient,
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
    setattr(N8nClient, f'build_{_operation.command_name}', _make_build_method(_operation.command_name))
    setattr(N8nClient, _operation.command_name, _make_call_method(_operation.command_name))


__all__ = ['N8nClient']
