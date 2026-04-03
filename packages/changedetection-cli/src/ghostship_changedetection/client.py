from __future__ import annotations

import base64
from typing import Any
from urllib.parse import quote

from ghostship_cli_contract import BaseHttpClient, RequestSpec


TEXT_CONTENT_TYPES = {
    "application/yaml",
    "application/x-yaml",
    "application/xml",
    "text/yaml",
    "text/xml",
}


def _compact_dict(data: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in data.items() if value is not None}


class ChangedetectionClient(BaseHttpClient):
    def __init__(self, base_url: str, api_key: str | None = None, *, default_timeout: float = 30.0):
        base = base_url.rstrip("/")
        if not base.endswith("/api/v1"):
            base = f"{base}/api/v1"
        headers = {"Accept": "application/json, text/plain, application/yaml, text/yaml, image/*, */*"}
        if api_key:
            headers["x-api-key"] = api_key
        super().__init__(base, default_headers=headers, default_timeout=default_timeout)

    def build_request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json_data: Any = None,
        content: str | bytes | None = None,
        headers: dict[str, Any] | None = None,
        timeout: float | None = None,
    ) -> RequestSpec:
        return self.build_request_spec(method, path, params=params, json_body=json_data, content=content, headers=headers, timeout=timeout)

    def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json_data: Any = None,
        content: str | bytes | None = None,
        headers: dict[str, Any] | None = None,
        timeout: float | None = None,
    ) -> Any:
        spec = self.build_request(method, path, params=params, json_data=json_data, content=content, headers=headers, timeout=timeout)
        response = BaseHttpClient.request(self, spec)
        return self._decode_response(response)

    def _decode_response(self, response: Any) -> Any:
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

    def list_watches(self, *, recheck_all: bool = False, tag: str | None = None, timeout: float | None = None) -> Any:
        params = _compact_dict({"recheck_all": "1" if recheck_all else None, "tag": tag})
        return self.request("GET", "/watch", params=params or None, timeout=timeout)

    def build_create_watch(self, body: dict[str, Any], *, timeout: float | None = None) -> RequestSpec:
        return self.build_request("POST", "/watch", json_data=body, timeout=timeout)

    def create_watch(self, body: dict[str, Any], *, timeout: float | None = None) -> Any:
        return self.request("POST", "/watch", json_data=body, timeout=timeout)

    def get_watch(
        self,
        uuid: str,
        *,
        recheck: bool = False,
        paused: str | None = None,
        muted: str | None = None,
        timeout: float | None = None,
    ) -> Any:
        params = _compact_dict({"recheck": "1" if recheck else None, "paused": paused, "muted": muted})
        return self.request("GET", f"/watch/{quote(uuid, safe='')}", params=params or None, timeout=timeout)

    def build_update_watch(self, uuid: str, body: dict[str, Any], *, timeout: float | None = None) -> RequestSpec:
        return self.build_request("PUT", f"/watch/{quote(uuid, safe='')}", json_data=body, timeout=timeout)

    def update_watch(self, uuid: str, body: dict[str, Any], *, timeout: float | None = None) -> Any:
        return self.request("PUT", f"/watch/{quote(uuid, safe='')}", json_data=body, timeout=timeout)

    def build_delete_watch(self, uuid: str, *, timeout: float | None = None) -> RequestSpec:
        return self.build_request("DELETE", f"/watch/{quote(uuid, safe='')}", timeout=timeout)

    def delete_watch(self, uuid: str, *, timeout: float | None = None) -> Any:
        return self.request("DELETE", f"/watch/{quote(uuid, safe='')}", timeout=timeout)

    def get_watch_history(self, uuid: str, *, timeout: float | None = None) -> Any:
        return self.request("GET", f"/watch/{quote(uuid, safe='')}/history", timeout=timeout)

    def get_watch_snapshot(self, uuid: str, timestamp: str, *, html: bool = False, timeout: float | None = None) -> Any:
        params = {"html": "1"} if html else None
        return self.request("GET", f"/watch/{quote(uuid, safe='')}/history/{quote(timestamp, safe='')}", params=params, timeout=timeout)

    def get_watch_history_diff(
        self,
        uuid: str,
        from_timestamp: str,
        to_timestamp: str,
        *,
        output_format: str | None = None,
        word_diff: str | None = None,
        no_markup: str | None = None,
        diff_type: str | None = None,
        changes_only: str | None = None,
        ignore_whitespace: str | None = None,
        removed: str | None = None,
        added: str | None = None,
        replaced: str | None = None,
        timeout: float | None = None,
    ) -> Any:
        params = _compact_dict(
            {
                "format": output_format,
                "word_diff": word_diff,
                "no_markup": no_markup,
                "type": diff_type,
                "changesOnly": changes_only,
                "ignoreWhitespace": ignore_whitespace,
                "removed": removed,
                "added": added,
                "replaced": replaced,
            }
        )
        return self.request(
            "GET",
            f"/watch/{quote(uuid, safe='')}/difference/{quote(from_timestamp, safe='')}/{quote(to_timestamp, safe='')}",
            params=params or None,
            timeout=timeout,
        )

    def get_watch_favicon(self, uuid: str, *, timeout: float | None = None) -> Any:
        return self.request("GET", f"/watch/{quote(uuid, safe='')}/favicon", timeout=timeout)

    def list_tags(self, *, timeout: float | None = None) -> Any:
        return self.request("GET", "/tags", timeout=timeout)

    def build_create_tag(self, body: dict[str, Any], *, timeout: float | None = None) -> RequestSpec:
        return self.build_request("POST", "/tag", json_data=body, timeout=timeout)

    def create_tag(self, body: dict[str, Any], *, timeout: float | None = None) -> Any:
        return self.request("POST", "/tag", json_data=body, timeout=timeout)

    def get_tag(self, uuid: str, *, muted: str | None = None, recheck: bool = False, timeout: float | None = None) -> Any:
        params = _compact_dict({"muted": muted, "recheck": "true" if recheck else None})
        return self.request("GET", f"/tag/{quote(uuid, safe='')}", params=params or None, timeout=timeout)

    def build_update_tag(self, uuid: str, body: dict[str, Any], *, timeout: float | None = None) -> RequestSpec:
        return self.build_request("PUT", f"/tag/{quote(uuid, safe='')}", json_data=body, timeout=timeout)

    def update_tag(self, uuid: str, body: dict[str, Any], *, timeout: float | None = None) -> Any:
        return self.request("PUT", f"/tag/{quote(uuid, safe='')}", json_data=body, timeout=timeout)

    def build_delete_tag(self, uuid: str, *, timeout: float | None = None) -> RequestSpec:
        return self.build_request("DELETE", f"/tag/{quote(uuid, safe='')}", timeout=timeout)

    def delete_tag(self, uuid: str, *, timeout: float | None = None) -> Any:
        return self.request("DELETE", f"/tag/{quote(uuid, safe='')}", timeout=timeout)

    def get_notifications(self, *, timeout: float | None = None) -> Any:
        return self.request("GET", "/notifications", timeout=timeout)

    def build_add_notifications(self, body: dict[str, Any], *, timeout: float | None = None) -> RequestSpec:
        return self.build_request("POST", "/notifications", json_data=body, timeout=timeout)

    def add_notifications(self, body: dict[str, Any], *, timeout: float | None = None) -> Any:
        return self.request("POST", "/notifications", json_data=body, timeout=timeout)

    def build_replace_notifications(self, body: dict[str, Any], *, timeout: float | None = None) -> RequestSpec:
        return self.build_request("PUT", "/notifications", json_data=body, timeout=timeout)

    def replace_notifications(self, body: dict[str, Any], *, timeout: float | None = None) -> Any:
        return self.request("PUT", "/notifications", json_data=body, timeout=timeout)

    def build_delete_notifications(self, body: dict[str, Any], *, timeout: float | None = None) -> RequestSpec:
        return self.build_request("DELETE", "/notifications", json_data=body, timeout=timeout)

    def delete_notifications(self, body: dict[str, Any], *, timeout: float | None = None) -> Any:
        return self.request("DELETE", "/notifications", json_data=body, timeout=timeout)

    def search_watches(self, query: str, *, tag: str | None = None, partial: str | None = None, timeout: float | None = None) -> Any:
        params = _compact_dict({"q": query, "tag": tag, "partial": partial})
        return self.request("GET", "/search", params=params, timeout=timeout)

    def build_import_watches(self, urls: list[str], *, params: dict[str, Any] | None = None, timeout: float | None = None) -> RequestSpec:
        return self.build_request("POST", "/import", params=params, content="\n".join(urls), headers={"Content-Type": "text/plain"}, timeout=timeout)

    def import_watches(self, urls: list[str], *, params: dict[str, Any] | None = None, timeout: float | None = None) -> Any:
        return self.request("POST", "/import", params=params, content="\n".join(urls), headers={"Content-Type": "text/plain"}, timeout=timeout)

    def get_system_info(self, *, timeout: float | None = None) -> Any:
        return self.request("GET", "/systeminfo", timeout=timeout)

    def get_full_api_spec(self, *, timeout: float | None = None) -> Any:
        return self.request("GET", "/full-spec", timeout=timeout)
