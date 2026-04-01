from __future__ import annotations

from dataclasses import dataclass, field, asdict, is_dataclass
import json
import os
from typing import Any, Mapping
from urllib.parse import urlencode

import httpx


KNOWN_FORMATS = ["Atom", "Html", "Json", "Mrss", "Plaintext", "Sfeed"]


def _parse_parameter_contexts(raw: Any) -> dict[str, dict[str, "BridgeParameterSpec"]]:
    parameters: dict[str, dict[str, BridgeParameterSpec]] = {}
    if isinstance(raw, Mapping):
        for context_name, context_params in raw.items():
            if not isinstance(context_params, Mapping):
                parameters[str(context_name)] = {}
                continue
            parameters[str(context_name)] = {
                str(param_name): BridgeParameterSpec.from_dict(param_data)
                for param_name, param_data in context_params.items()
                if isinstance(param_data, Mapping)
            }
        return parameters

    if isinstance(raw, list):
        merged: dict[str, BridgeParameterSpec] = {}
        for item in raw:
            if not isinstance(item, Mapping):
                continue
            for param_name, param_data in item.items():
                if isinstance(param_data, Mapping):
                    merged[str(param_name)] = BridgeParameterSpec.from_dict(param_data)
        parameters["global"] = merged
        return parameters

    return parameters


def _cloudflare_access_headers() -> dict[str, str]:
    headers: dict[str, str] = {}
    client_id = os.getenv("GHOSTSHIP_TEST_CF_ACCESS_CLIENT_ID")
    client_secret = os.getenv("GHOSTSHIP_TEST_CF_ACCESS_CLIENT_SECRET")
    if client_id:
        headers["CF-Access-Client-Id"] = client_id
    if client_secret:
        headers["CF-Access-Client-Secret"] = client_secret
    return headers


@dataclass(slots=True)
class BridgeParameterSpec:
    name: str | None = None
    type: str | None = None
    required: bool | None = None
    default_value: Any = None
    example_value: Any = None
    title: str | None = None
    pattern: str | None = None
    values: dict[str, Any] | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "BridgeParameterSpec":
        known = {"name", "type", "required", "defaultValue", "exampleValue", "title", "pattern", "values"}
        return cls(
            name=data.get("name"),
            type=data.get("type"),
            required=data.get("required"),
            default_value=data.get("defaultValue"),
            example_value=data.get("exampleValue"),
            title=data.get("title"),
            pattern=data.get("pattern"),
            values=dict(data["values"]) if isinstance(data.get("values"), Mapping) else None,
            extra={k: v for k, v in data.items() if k not in known},
        )

    def to_dict(self) -> dict[str, Any]:
        data = {
            "name": self.name,
            "type": self.type,
            "required": self.required,
            "defaultValue": self.default_value,
            "exampleValue": self.example_value,
            "title": self.title,
            "pattern": self.pattern,
            "values": self.values,
        }
        data.update(self.extra)
        return {k: v for k, v in data.items() if v is not None}


@dataclass(slots=True)
class BridgeSpec:
    name: str
    status: str
    uri: str | None = None
    donation_uri: str | None = None
    display_name: str | None = None
    icon: str | None = None
    parameters: dict[str, dict[str, BridgeParameterSpec]] = field(default_factory=dict)
    maintainer: str | None = None
    description: str | None = None

    @classmethod
    def from_dict(cls, name: str, data: Mapping[str, Any]) -> "BridgeSpec":
        parameters = _parse_parameter_contexts(data.get("parameters", {}))
        return cls(
            name=name,
            status=str(data.get("status", "inactive")),
            uri=data.get("uri"),
            donation_uri=data.get("donationUri"),
            display_name=data.get("name"),
            icon=data.get("icon"),
            parameters=parameters,
            maintainer=data.get("maintainer"),
            description=data.get("description"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status,
            "uri": self.uri,
            "donationUri": self.donation_uri,
            "display_name": self.display_name,
            "icon": self.icon,
            "parameters": {
                context: {key: value.to_dict() for key, value in specs.items()}
                for context, specs in self.parameters.items()
            },
            "maintainer": self.maintainer,
            "description": self.description,
        }


@dataclass(slots=True)
class BridgeListResponse:
    bridges: dict[str, BridgeSpec]
    total: int

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "BridgeListResponse":
        bridges = {
            name: BridgeSpec.from_dict(name, bridge)
            for name, bridge in dict(data.get("bridges", {})).items()
            if isinstance(bridge, Mapping)
        }
        return cls(bridges=bridges, total=int(data.get("total", len(bridges))))

    def to_dict(self) -> dict[str, Any]:
        return {"bridges": {k: v.to_dict() for k, v in self.bridges.items()}, "total": self.total}


@dataclass(slots=True)
class FeedCandidate:
    url: str
    bridge_params: dict[str, Any]
    bridge_data: dict[str, Any]
    bridge_meta: dict[str, Any]

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "FeedCandidate":
        return cls(
            url=str(data.get("url", "")),
            bridge_params=dict(data.get("bridgeParams", {})),
            bridge_data=dict(data.get("bridgeData", {})),
            bridge_meta=dict(data.get("bridgeMeta", {})),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "url": self.url,
            "bridgeParams": self.bridge_params,
            "bridgeData": self.bridge_data,
            "bridgeMeta": self.bridge_meta,
        }


@dataclass(slots=True)
class DetectResult:
    status_code: int
    location: str | None

    def to_dict(self) -> dict[str, Any]:
        return {"status_code": self.status_code, "location": self.location}


@dataclass(slots=True)
class DisplayResult:
    url: str
    status_code: int
    content_type: str | None
    body: str
    parsed: Any = None

    def to_dict(self) -> dict[str, Any]:
        data = {
            "url": self.url,
            "status_code": self.status_code,
            "content_type": self.content_type,
            "body": self.body,
        }
        if self.parsed is not None:
            data["parsed"] = self.parsed
        return data


@dataclass(slots=True)
class BuildUrlResult:
    url: str
    bridge: str
    format: str
    context: str | None
    parameters: dict[str, str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "url": self.url,
            "bridge": self.bridge,
            "format": self.format,
            "context": self.context,
            "parameters": self.parameters,
        }


def to_jsonable(value: Any) -> Any:
    if hasattr(value, "to_dict"):
        return value.to_dict()
    if is_dataclass(value):
        return asdict(value)
    if isinstance(value, list):
        return [to_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {key: to_jsonable(item) for key, item in value.items()}
    return value


class RssBridgeClient:
    def __init__(self, base_url: str, timeout: float = 30.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.headers = _cloudflare_access_headers()
        self.headers["Accept"] = "application/json, text/plain, application/xml, text/xml, */*"

    def _request_json(self, params: Mapping[str, Any]) -> Any:
        with httpx.Client(headers=self.headers, timeout=self.timeout, follow_redirects=False) as client:
            response = client.get(f"{self.base_url}/", params=params)
            response.raise_for_status()
            return response.json()

    def list_bridges(self) -> BridgeListResponse:
        return BridgeListResponse.from_dict(self._request_json({"action": "list"}))

    def get_bridge(self, bridge: str) -> BridgeSpec:
        bridges = self.list_bridges().bridges
        if bridge not in bridges:
            raise KeyError(f"bridge not found: {bridge}")
        return bridges[bridge]

    def build_display_url(
        self,
        *,
        bridge: str,
        format: str,
        context: str | None = None,
        parameters: Mapping[str, str] | None = None,
    ) -> str:
        query: dict[str, str] = {"action": "display", "bridge": bridge}
        if context:
            query["context"] = context
        query["format"] = format
        if parameters:
            for key in sorted(parameters):
                query[key] = parameters[key]
        return f"{self.base_url}/?{urlencode(query)}"

    def build_url_result(
        self,
        *,
        bridge: str,
        format: str,
        context: str | None = None,
        parameters: Mapping[str, str] | None = None,
    ) -> BuildUrlResult:
        return BuildUrlResult(
            url=self.build_display_url(bridge=bridge, format=format, context=context, parameters=parameters),
            bridge=bridge,
            format=format,
            context=context,
            parameters=dict(parameters or {}),
        )

    def find_feed(self, url: str, *, format: str) -> list[FeedCandidate]:
        payload = self._request_json({"action": "findfeed", "url": url, "format": format})
        return [FeedCandidate.from_dict(item) for item in payload]

    def detect(self, url: str, *, format: str) -> DetectResult:
        with httpx.Client(headers=self.headers, timeout=self.timeout, follow_redirects=False) as client:
            response = client.get(f"{self.base_url}/", params={"action": "detect", "url": url, "format": format})
            location = response.headers.get("location")
        return DetectResult(status_code=response.status_code, location=location)

    def display(
        self,
        *,
        bridge: str,
        format: str,
        context: str | None = None,
        parameters: Mapping[str, str] | None = None,
    ) -> DisplayResult:
        url = self.build_display_url(bridge=bridge, format=format, context=context, parameters=parameters)
        return self.fetch_url(url)

    def fetch_url(self, url: str) -> DisplayResult:
        with httpx.Client(headers=self.headers, timeout=self.timeout, follow_redirects=True) as client:
            response = client.get(url)
            response.raise_for_status()
            content_type = response.headers.get("content-type")
            parsed = None
            if content_type and "json" in content_type.lower():
                try:
                    parsed = response.json()
                except json.JSONDecodeError:
                    parsed = None
        return DisplayResult(
            url=str(response.url),
            status_code=response.status_code,
            content_type=content_type,
            body=response.text,
            parsed=parsed,
        )
