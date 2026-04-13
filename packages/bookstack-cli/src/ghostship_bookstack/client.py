from __future__ import annotations

from typing import Any, Mapping
from urllib.parse import quote

import httpx

from ghostship_cli_contract import BaseHttpClient, InvalidInputError, RequestSpec, decode_response

from .catalog import OPERATIONS, OPERATIONS_BY_COMMAND, OperationDef


class BookStackClient(BaseHttpClient):
    def __init__(self, base_url: str, token_id: str, token_secret: str, *, default_timeout: float = 30.0, transport: httpx.BaseTransport | None = None):
        normalized_base = base_url.rstrip('/')
        if normalized_base.endswith('/api'):
            api_base = normalized_base
        else:
            api_base = f"{normalized_base}/api"
        headers = {
            'Accept': 'application/json, text/plain, text/html, image/*, application/octet-stream, application/zip, */*',
            'Authorization': f'Token {token_id}:{token_secret}',
        }
        super().__init__(api_base, default_headers=headers, default_timeout=default_timeout, transport=transport)

    def _normalize_params(
        self,
        *,
        params: Mapping[str, Any] | None = None,
        query_params: Mapping[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        if params is not None and query_params is not None:
            left = dict(params)
            right = dict(query_params)
            if left != right:
                raise InvalidInputError('use either params or query_params, not both')
            return left
        merged = params if params is not None else query_params
        return dict(merged) if merged is not None else None

    def build_request(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        query_params: Mapping[str, Any] | None = None,
        json_body: Any = None,
        content: str | bytes | None = None,
        form_data: Mapping[str, Any] | None = None,
        files: dict[str, Any] | list[Any] | None = None,
        headers: Mapping[str, Any] | None = None,
        timeout: float | None = None,
    ) -> RequestSpec:
        actual_method = method.upper()
        actual_form_data = dict(form_data) if form_data is not None else None
        normalized_params = self._normalize_params(params=params, query_params=query_params)
        if (actual_form_data is not None or files is not None) and actual_method != 'POST':
            actual_form_data = dict(actual_form_data or {})
            actual_form_data['_method'] = actual_method
            actual_method = 'POST'
        return self.build_request_spec(
            actual_method,
            path,
            params=normalized_params,
            json_body=json_body,
            content=content,
            form_data=actual_form_data,
            files=files,
            headers=dict(headers) if headers is not None else None,
            timeout=timeout,
        )

    def request(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        query_params: Mapping[str, Any] | None = None,
        json_body: Any = None,
        content: str | bytes | None = None,
        form_data: Mapping[str, Any] | None = None,
        files: dict[str, Any] | list[Any] | None = None,
        headers: Mapping[str, Any] | None = None,
        timeout: float | None = None,
    ) -> Any:
        spec = self.build_request(
            method,
            path,
            params=params,
            query_params=query_params,
            json_body=json_body,
            content=content,
            form_data=form_data,
            files=files,
            headers=headers,
            timeout=timeout,
        )
        return decode_response(BaseHttpClient.request(self, spec))

    def request_response(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        query_params: Mapping[str, Any] | None = None,
        json_body: Any = None,
        content: str | bytes | None = None,
        form_data: Mapping[str, Any] | None = None,
        files: dict[str, Any] | list[Any] | None = None,
        headers: Mapping[str, Any] | None = None,
        timeout: float | None = None,
    ) -> httpx.Response:
        spec = self.build_request(
            method,
            path,
            params=params,
            query_params=query_params,
            json_body=json_body,
            content=content,
            form_data=form_data,
            files=files,
            headers=headers,
            timeout=timeout,
        )
        return BaseHttpClient.request(self, spec)

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
        form_data: Mapping[str, Any] | None = None,
        files: dict[str, Any] | list[Any] | None = None,
        timeout: float | None = None,
    ) -> RequestSpec:
        operation = OPERATIONS_BY_COMMAND[command_name]
        if json_body is not None and (form_data is not None or files is not None):
            raise InvalidInputError('use either json_body or form_data/files, not both')
        if (json_body is not None or form_data is not None or files is not None) and not operation.has_body:
            raise InvalidInputError(f"{command_name} does not accept a request body")
        return self.build_request(
            operation.method,
            self._render_path(operation, path_params),
            query_params=query_params,
            json_body=json_body,
            form_data=form_data,
            files=files,
            timeout=timeout,
        )

    def request_operation(
        self,
        command_name: str,
        *,
        path_params: Mapping[str, Any] | None = None,
        query_params: Mapping[str, Any] | None = None,
        json_body: Any = None,
        form_data: Mapping[str, Any] | None = None,
        files: dict[str, Any] | list[Any] | None = None,
        timeout: float | None = None,
    ) -> Any:
        operation = OPERATIONS_BY_COMMAND[command_name]
        spec = self.build_operation_request(
            command_name,
            path_params=path_params,
            query_params=query_params,
            json_body=json_body,
            form_data=form_data,
            files=files,
            timeout=timeout,
        )
        if operation.response_kind == 'json':
            return self.request_json(spec.method, spec.path, params=spec.params, json_body=spec.json_body, content=spec.content, form_data=spec.form_data, files=spec.files, headers=spec.headers, timeout=spec.timeout)
        if operation.response_kind == 'text':
            return self.request(spec.method, spec.path, params=spec.params, json_body=spec.json_body, content=spec.content, form_data=spec.form_data, files=spec.files, headers=spec.headers, timeout=spec.timeout)
        return BaseHttpClient.request(self, spec)


def _make_build_method(command_name: str):
    def _method(
        self: BookStackClient,
        *,
        path_params: Mapping[str, Any] | None = None,
        query_params: Mapping[str, Any] | None = None,
        json_body: Any = None,
        form_data: Mapping[str, Any] | None = None,
        files: dict[str, Any] | list[Any] | None = None,
        timeout: float | None = None,
    ) -> RequestSpec:
        return self.build_operation_request(
            command_name,
            path_params=path_params,
            query_params=query_params,
            json_body=json_body,
            form_data=form_data,
            files=files,
            timeout=timeout,
        )

    _method.__name__ = f'build_{command_name}'
    return _method


def _make_call_method(command_name: str):
    def _method(
        self: BookStackClient,
        *,
        path_params: Mapping[str, Any] | None = None,
        query_params: Mapping[str, Any] | None = None,
        json_body: Any = None,
        form_data: Mapping[str, Any] | None = None,
        files: dict[str, Any] | list[Any] | None = None,
        timeout: float | None = None,
    ) -> Any:
        return self.request_operation(
            command_name,
            path_params=path_params,
            query_params=query_params,
            json_body=json_body,
            form_data=form_data,
            files=files,
            timeout=timeout,
        )

    _method.__name__ = command_name
    return _method


for _operation in OPERATIONS:
    setattr(BookStackClient, f'build_{_operation.command_name}', _make_build_method(_operation.command_name))
    setattr(BookStackClient, _operation.command_name, _make_call_method(_operation.command_name))


__all__ = ['BookStackClient']
