from __future__ import annotations

import json

from typer.testing import CliRunner

from ghostship_changedetection import cli


runner = CliRunner()


class DummyClient:
    def __init__(self) -> None:
        self.calls: list[tuple] = []

    def build_create_tag(self, body, *, timeout=None):
        class _Spec:
            def __init__(self, payload):
                self.payload = payload

            def to_dict(self):
                return self.payload

        return _Spec({"method": "POST", "path": "/tag", "timeout": timeout, "json_body": body})

    def create_tag(self, body, *, timeout=None):
        self.calls.append(("create_tag", body, timeout))
        return {"uuid": "tag-1"}

    def build_import_watches(self, urls, *, params=None, timeout=None):
        class _Spec:
            def __init__(self, payload):
                self.payload = payload

            def to_dict(self):
                return self.payload

        return _Spec({"method": "POST", "path": "/import", "timeout": timeout, "params": params, "content": "\n".join(urls), "headers": {"Content-Type": "text/plain"}})

    def import_watches(self, urls, *, params=None, timeout=None):
        self.calls.append(("import_watches", urls, params, timeout))
        return ["watch-1"]

    def list_watches(self, *, recheck_all=False, tag=None, timeout=None):
        self.calls.append(("list_watches", recheck_all, tag, timeout))
        return {"watch-1": {"title": "Example"}}

    def get_full_api_spec(self, *, timeout=None):
        self.calls.append(("get_full_api_spec", timeout))
        return {"content_type": "application/yaml", "body": "openapi: 3.1.0"}

    def build_request(self, method, path, *, params=None, json_data=None, content=None, headers=None, timeout=None):
        class _Spec:
            def __init__(self, payload):
                self.payload = payload

            def to_dict(self):
                return self.payload

        return _Spec(
            {
                "method": method,
                "path": path if path.startswith("/") else f"/{path}",
                "params": params,
                "json_body": json_data,
                "content": content,
                "headers": headers,
                "timeout": timeout,
            }
        )

    def request(self, method, path, *, params=None, json_data=None, content=None, headers=None, timeout=None):
        self.calls.append(("request", method, path, params, json_data, content, headers, timeout))
        return {"ok": True}


def test_timeout_applies(monkeypatch):
    client = DummyClient()
    monkeypatch.setattr(cli, "get_client", lambda require_api_key=True: client)
    result = runner.invoke(cli.app, ["--timeout", "9", "list_watches"])
    assert result.exit_code == 0
    assert client.calls[-1] == ("list_watches", False, None, 9.0)


def test_create_tag_dry_run(monkeypatch):
    client = DummyClient()
    monkeypatch.setattr(cli, "get_client", lambda require_api_key=True: client)
    result = runner.invoke(cli.app, ["create_tag", "--body-json", '{"title":"Production"}', "--dry-run"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["path"] == "/tag"
    assert payload["json_body"]["title"] == "Production"
    assert not client.calls


def test_import_watches_dry_run(monkeypatch):
    client = DummyClient()
    monkeypatch.setattr(cli, "get_client", lambda require_api_key=True: client)
    result = runner.invoke(cli.app, ["import_watches", "https://example.com", "https://example.org", "--tag", "production", "--dry-run"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["path"] == "/import"
    assert payload["content"] == "https://example.com\nhttps://example.org"
    assert payload["params"]["tag"] == "production"


def test_get_full_api_spec_can_skip_api_key(monkeypatch):
    client = DummyClient()

    def _get_client(require_api_key=True):
        assert require_api_key is False
        return client

    monkeypatch.setattr(cli, "get_client", _get_client)
    result = runner.invoke(cli.app, ["get_full_api_spec"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["content_type"] == "application/yaml"


def test_request_full_spec_without_leading_slash_can_skip_api_key(monkeypatch):
    client = DummyClient()

    def _get_client(require_api_key=True):
        assert require_api_key is False
        return client

    monkeypatch.setattr(cli, "get_client", _get_client)
    result = runner.invoke(cli.app, ["request", "GET", "full-spec"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
