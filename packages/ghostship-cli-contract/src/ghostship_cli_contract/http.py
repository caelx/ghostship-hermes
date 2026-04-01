from __future__ import annotations

import json
import os
from typing import Any

import httpx

from .errors import HttpStatusError, ResponseDecodeError, TimeoutError, TransportError
from .models import RequestSpec

DEFAULT_TIMEOUT = 30.0


def cloudflare_access_headers() -> dict[str, str]:
    headers: dict[str, str] = {}
    client_id = os.getenv("GHOSTSHIP_TEST_CF_ACCESS_CLIENT_ID")
    client_secret = os.getenv("GHOSTSHIP_TEST_CF_ACCESS_CLIENT_SECRET")
    if client_id:
        headers["CF-Access-Client-Id"] = client_id
    if client_secret:
        headers["CF-Access-Client-Secret"] = client_secret
    return headers


class BaseHttpClient:
    def __init__(self, base_url: str, *, default_headers: dict[str, str] | None = None, default_timeout: float = DEFAULT_TIMEOUT, transport: httpx.BaseTransport | None = None, follow_redirects: bool = False):
        self.base_url = base_url.rstrip('/')
        self.default_headers = {**cloudflare_access_headers(), **(default_headers or {})}
        self.default_timeout = default_timeout
        self.transport = transport
        self.follow_redirects = follow_redirects

    def build_request_spec(self, method: str, path: str, *, params: dict[str, Any] | None = None, json_body: Any = None, form_data: dict[str, Any] | None = None, files: dict[str, Any] | list[Any] | None = None, headers: dict[str, Any] | None = None, timeout: float | None = None) -> RequestSpec:
        merged_headers = {**self.default_headers, **(headers or {})}
        return RequestSpec(method=method.upper(), path=path if path.startswith('/') else f'/{path}', timeout=float(timeout if timeout is not None else self.default_timeout), params=params, json_body=json_body, form_data=form_data, files=files, headers=merged_headers or None)

    def _client(self, timeout: float) -> httpx.Client:
        return httpx.Client(headers=self.default_headers, timeout=timeout, transport=self.transport, follow_redirects=self.follow_redirects)

    def request(self, spec: RequestSpec) -> httpx.Response:
        url = f"{self.base_url}{spec.path}"
        try:
            with self._client(spec.timeout) as client:
                response = client.request(spec.method, url, params=spec.params, json=spec.json_body, data=spec.form_data, files=spec.files, headers=spec.headers)
        except httpx.TimeoutException as exc:
            raise TimeoutError(f"request timed out after {spec.timeout} seconds", details={"method": spec.method, "path": spec.path, "timeout": spec.timeout}) from exc
        except httpx.HTTPError as exc:
            raise TransportError(str(exc), details={"method": spec.method, "path": spec.path}) from exc
        if response.is_error:
            details: Any = None
            try:
                details = response.json()
            except Exception:
                details = response.text or None
            raise HttpStatusError(f"remote service returned HTTP {response.status_code}", status_code=response.status_code, details=details)
        return response

    def request_json(self, method: str, path: str, *, params: dict[str, Any] | None = None, json_body: Any = None, form_data: dict[str, Any] | None = None, files: dict[str, Any] | list[Any] | None = None, headers: dict[str, Any] | None = None, timeout: float | None = None) -> Any:
        spec = self.build_request_spec(method, path, params=params, json_body=json_body, form_data=form_data, files=files, headers=headers, timeout=timeout)
        response = BaseHttpClient.request(self, spec)
        if not response.content:
            return {"status": "success"}
        try:
            return response.json()
        except json.JSONDecodeError as exc:
            raise ResponseDecodeError('response did not contain valid JSON', details={"method": spec.method, "path": spec.path}) from exc
