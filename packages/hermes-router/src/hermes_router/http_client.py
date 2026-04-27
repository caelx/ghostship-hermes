from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import httpx


class RouterHttpError(Exception):
    def __init__(self, message: str, *, details: Any = None):
        super().__init__(message)
        self.message = message
        self.details = details


class TimeoutError(RouterHttpError):
    pass


class TransportError(RouterHttpError):
    pass


class ResponseDecodeError(RouterHttpError):
    pass


class HttpStatusError(RouterHttpError):
    def __init__(self, message: str, *, status_code: int, details: Any = None, headers: dict[str, str] | None = None):
        super().__init__(message, details=details)
        self.status_code = status_code
        self.headers = headers or None


@dataclass(slots=True)
class RequestSpec:
    method: str
    path: str
    timeout: float
    params: dict[str, Any] | None = None
    json_body: Any = None
    headers: dict[str, Any] | None = None


def _cloudflare_access_headers() -> dict[str, str]:
    headers: dict[str, str] = {}
    client_id = os.getenv("GHOSTSHIP_TEST_CF_ACCESS_CLIENT_ID")
    client_secret = os.getenv("GHOSTSHIP_TEST_CF_ACCESS_CLIENT_SECRET")
    if client_id:
        headers["CF-Access-Client-Id"] = client_id
    if client_secret:
        headers["CF-Access-Client-Secret"] = client_secret
    return headers


def _response_error_details(response: httpx.Response) -> Any:
    location = response.headers.get("location")
    if not response.content:
        return {"location": location} if location else None
    try:
        return response.json()
    except Exception:
        text = response.text or None
        if location and text:
            return {"location": location, "body": text}
        if location:
            return {"location": location}
        return text


class BaseHttpClient:
    def __init__(
        self,
        base_url: str,
        *,
        default_headers: dict[str, str] | None = None,
        default_timeout: float = 30.0,
        transport: httpx.BaseTransport | None = None,
        follow_redirects: bool = False,
    ):
        self.base_url = base_url.rstrip("/")
        self.default_headers = {**_cloudflare_access_headers(), **(default_headers or {})}
        self.default_timeout = default_timeout
        self.transport = transport
        self.follow_redirects = follow_redirects

    def build_request_spec(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json_body: Any = None,
        headers: dict[str, Any] | None = None,
        timeout: float | None = None,
    ) -> RequestSpec:
        merged_headers = {**self.default_headers, **(headers or {})}
        return RequestSpec(
            method=method.upper(),
            path=path if path.startswith("/") else f"/{path}",
            timeout=float(timeout if timeout is not None else self.default_timeout),
            params=params,
            json_body=json_body,
            headers=merged_headers or None,
        )

    def _client(self, timeout: float) -> httpx.Client:
        return httpx.Client(
            headers=self.default_headers,
            timeout=timeout,
            transport=self.transport,
            follow_redirects=self.follow_redirects,
        )

    def request(self, spec: RequestSpec) -> httpx.Response:
        url = f"{self.base_url}{spec.path}"
        try:
            with self._client(spec.timeout) as client:
                response = client.request(
                    spec.method,
                    url,
                    params=spec.params,
                    json=spec.json_body,
                    headers=spec.headers,
                )
        except httpx.TimeoutException as exc:
            raise TimeoutError(
                f"request timed out after {spec.timeout} seconds",
                details={"method": spec.method, "path": spec.path, "timeout": spec.timeout},
            ) from exc
        except httpx.HTTPError as exc:
            raise TransportError(str(exc), details={"method": spec.method, "path": spec.path}) from exc
        if not response.is_success:
            raise HttpStatusError(
                f"remote service returned HTTP {response.status_code}",
                status_code=response.status_code,
                details=_response_error_details(response),
                headers=dict(response.headers),
            )
        return response

    def request_response(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json_body: Any = None,
        headers: dict[str, Any] | None = None,
        timeout: float | None = None,
    ) -> httpx.Response:
        spec = self.build_request_spec(
            method,
            path,
            params=params,
            json_body=json_body,
            headers=headers,
            timeout=timeout,
        )
        return self.request(spec)

    def request_json(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json_body: Any = None,
        headers: dict[str, Any] | None = None,
        timeout: float | None = None,
    ) -> Any:
        response = self.request_response(
            method,
            path,
            params=params,
            json_body=json_body,
            headers=headers,
            timeout=timeout,
        )
        if not response.content:
            return {"status": "success"}
        try:
            return response.json()
        except ValueError as exc:
            raise ResponseDecodeError(
                "response did not contain valid JSON",
                details={"method": method.upper(), "path": path if path.startswith("/") else f"/{path}"},
            ) from exc
