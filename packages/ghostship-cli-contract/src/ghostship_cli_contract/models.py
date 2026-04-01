from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


def _copy_mapping(data: Mapping[str, Any] | None) -> dict[str, Any] | None:
    if data is None:
        return None
    return dict(data)


def _serialize_file_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _serialize_file_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_serialize_file_value(item) for item in value]
    if isinstance(value, tuple):
        if len(value) >= 2:
            filename = value[0]
            content_type = value[2] if len(value) >= 3 else None
            payload: dict[str, Any] = {'filename': filename}
            if content_type is not None:
                payload['content_type'] = content_type
            return payload
        return list(value)
    return value


@dataclass(slots=True)
class RequestSpec:
    method: str
    path: str
    timeout: float
    params: dict[str, Any] | None = None
    json_body: Any = None
    form_data: dict[str, Any] | None = None
    files: dict[str, Any] | list[Any] | None = None
    headers: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            'method': self.method.upper(),
            'path': self.path,
            'timeout': self.timeout,
        }
        optional = {
            'params': _copy_mapping(self.params),
            'json_body': self.json_body,
            'form_data': _copy_mapping(self.form_data),
            'files': _serialize_file_value(self.files),
            'headers': _copy_mapping(self.headers),
        }
        for key, value in optional.items():
            if value not in (None, {}, []):
                payload[key] = value
        return payload
