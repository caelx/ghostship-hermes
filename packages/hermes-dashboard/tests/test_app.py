from __future__ import annotations

import importlib
from pathlib import Path

from fastapi.testclient import TestClient


def _load_app_module(monkeypatch, tmp_path: Path):
    managed_home = tmp_path / ".hermes"
    managed_home.mkdir(parents=True)
    (managed_home / "config.yaml").write_text(
        "model:\n  provider: auto\n  default: coding\n  base_url: http://127.0.0.1:8788/v1\n",
        encoding="utf-8",
    )
    (managed_home / ".env").write_text("OPENAI_API_KEY=test-token\n", encoding="utf-8")
    (managed_home / "SOUL.md").write_text("seeded soul\n", encoding="utf-8")
    (managed_home / "auth.json").write_text('{"provider":"codex"}\n', encoding="utf-8")
    (managed_home / "gateway.pid").write_text('{"pid":123,"kind":"hermes-gateway"}\n', encoding="utf-8")

    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("HERMES_HOME", str(managed_home))
    monkeypatch.setenv("GHOSTSHIP_DASHBOARD_STATE_DIR", str(tmp_path / "state"))
    monkeypatch.setenv("GHOSTSHIP_HERMES_GATEWAY_SERVICE", "ghostship-hermes-gateway.service")
    monkeypatch.setenv("GHOSTSHIP_TERMINAL_CWD", "/workspace")

    import hermes_dashboard.app as app_module

    app_module = importlib.reload(app_module)
    app_module.fetch_router_enrichment = lambda *_args, **_kwargs: {"ready": True, "aliases": [], "providers": []}
    return app_module


def test_environment_payload_reports_single_agent(monkeypatch, tmp_path: Path) -> None:
    app_module = _load_app_module(monkeypatch, tmp_path)

    payload = app_module.current_environment_payload()

    assert "profiles" not in payload
    assert "default_profile" not in payload
    assert payload["gateway_service"] == "ghostship-hermes-gateway.service"
    assert payload["agent"]["name"] == "Managed Agent"
    assert payload["agent"]["path"] == str(tmp_path / ".hermes")
    assert payload["agent"]["service"] == "ghostship-hermes-gateway.service"
    assert payload["agent"]["has_config"] is True
    assert payload["agent"]["has_env"] is True
    assert payload["agent"]["has_auth"] is True
    assert payload["agent"]["has_soul"] is True
    assert payload["agent"]["has_gateway_pid"] is True


def test_status_api_uses_single_agent_contract(monkeypatch, tmp_path: Path) -> None:
    app_module = _load_app_module(monkeypatch, tmp_path)
    client = TestClient(app_module.app)

    response = client.get("/api/status")

    assert response.status_code == 200
    payload = response.json()
    assert "profiles" not in payload
    assert "default_profile" not in payload
    assert payload["environment"]["agent"]["service"] == "ghostship-hermes-gateway.service"
    assert payload["environment"]["model"] == "coding"
    assert payload["environment"]["dashboard_bind"] == "0.0.0.0:7681"


def test_home_page_uses_agent_label_not_profiles(monkeypatch, tmp_path: Path) -> None:
    app_module = _load_app_module(monkeypatch, tmp_path)
    client = TestClient(app_module.app)

    response = client.get("/")

    assert response.status_code == 200
    assert "Agent" in response.text
    assert "Profiles" not in response.text
