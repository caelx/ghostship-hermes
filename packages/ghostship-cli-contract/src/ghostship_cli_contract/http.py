from __future__ import annotations

import base64
import json
import os
from typing import Any

import httpx

from .errors import HttpStatusError, ResponseDecodeError, TimeoutError, TransportError
from .models import RequestSpec

DEFAULT_TIMEOUT = 30.0
TEXT_CONTENT_TYPES = {
    "application/yaml",
    "application/x-yaml",
    "application/xml",
    "text/yaml",
    "text/xml",
}


def cloudflare_access_headers() -> dict[str, str]:
    headers: dict[str, str] = {}
    client_id = os.getenv("GHOSTSHIP_TEST_CF_ACCESS_CLIENT_ID")
    client_secret = os.getenv("GHOSTSHIP_TEST_CF_ACCESS_CLIENT_SECRET")
    if client_id:
        headers["CF-Access-Client-Id"] = client_id
    if client_secret:
        headers["CF-Access-Client-Secret"] = client_secret
    return headers


def decode_response(response: httpx.Response) -> Any:
    if not response.content:
        return {"status": "success"}

    content_type = response.headers.get("content-type", "").split(";", 1)[0].strip() or None
    if content_type == "application/json":
        return response.json()
    if content_type and (content_type.startswith("text/") or content_type in TEXT_CONTENT_TYPES):
        return {"content_type": content_type, "body": response.text}
    if content_type and content_type.startswith("image/"):
        return {
            "content_type": content_type,
            "encoding": "base64",
            "body_base64": base64.b64encode(response.content).decode("ascii"),
        }

    try:
        return response.json()
    except ValueError:
        return {
            "content_type": content_type,
            "encoding": "base64",
            "body_base64": base64.b64encode(response.content).decode("ascii"),
        }


class BaseHttpClient:
    def __init__(self, base_url: str, *, default_headers: dict[str, str] | None = None, default_timeout: float = DEFAULT_TIMEOUT, transport: httpx.BaseTransport | None = None, follow_redirects: bool = False):
        self.base_url = base_url.rstrip('/')
        self.default_headers = {**cloudflare_access_headers(), **(default_headers or {})}
        self.default_timeout = default_timeout
        self.transport = transport
        self.follow_redirects = follow_redirects

    def build_request_spec(self, method: str, path: str, *, params: dict[str, Any] | None = None, json_body: Any = None, content: str | bytes | None = None, form_data: dict[str, Any] | None = None, files: dict[str, Any] | list[Any] | None = None, headers: dict[str, Any] | None = None, timeout: float | None = None) -> RequestSpec:
        merged_headers = {**self.default_headers, **(headers or {})}
        return RequestSpec(method=method.upper(), path=path if path.startswith('/') else f'/{path}', timeout=float(timeout if timeout is not None else self.default_timeout), params=params, json_body=json_body, content=content, form_data=form_data, files=files, headers=merged_headers or None)

    def _client(self, timeout: float) -> httpx.Client:
        return httpx.Client(headers=self.default_headers, timeout=timeout, transport=self.transport, follow_redirects=self.follow_redirects)

    def request(self, spec: RequestSpec) -> httpx.Response:
        url = f"{self.base_url}{spec.path}"
        try:
            with self._client(spec.timeout) as client:
                response = client.request(
                    spec.method,
                    url,
                    params=spec.params,
                    json=spec.json_body,
                    content=spec.content,
                    data=spec.form_data,
                    files=spec.files,
                    headers=spec.headers,
                )
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
            raise HttpStatusError(
                f"remote service returned HTTP {response.status_code}",
                status_code=response.status_code,
                details=details,
                headers=dict(response.headers),
            )
        return response

    def request_response(self, method: str, path: str, *, params: dict[str, Any] | None = None, json_body: Any = None, content: str | bytes | None = None, form_data: dict[str, Any] | None = None, files: dict[str, Any] | list[Any] | None = None, headers: dict[str, Any] | None = None, timeout: float | None = None) -> httpx.Response:
        spec = self.build_request_spec(method, path, params=params, json_body=json_body, content=content, form_data=form_data, files=files, headers=headers, timeout=timeout)
        return BaseHttpClient.request(self, spec)

    def request_decoded(self, method: str, path: str, *, params: dict[str, Any] | None = None, json_body: Any = None, content: str | bytes | None = None, form_data: dict[str, Any] | None = None, files: dict[str, Any] | list[Any] | None = None, headers: dict[str, Any] | None = None, timeout: float | None = None) -> Any:
        response = self.request_response(method, path, params=params, json_body=json_body, content=content, form_data=form_data, files=files, headers=headers, timeout=timeout)
        return decode_response(response)

    def request_json(self, method: str, path: str, *, params: dict[str, Any] | None = None, json_body: Any = None, content: str | bytes | None = None, form_data: dict[str, Any] | None = None, files: dict[str, Any] | list[Any] | None = None, headers: dict[str, Any] | None = None, timeout: float | None = None) -> Any:
        spec = self.build_request_spec(method, path, params=params, json_body=json_body, content=content, form_data=form_data, files=files, headers=headers, timeout=timeout)
        response = BaseHttpClient.request(self, spec)
        if not response.content:
            return {"status": "success"}
        try:
            return response.json()
        except json.JSONDecodeError as exc:
            raise ResponseDecodeError('response did not contain valid JSON', details={"method": spec.method, "path": spec.path}) from exc
