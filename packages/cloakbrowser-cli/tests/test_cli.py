import json
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from ghostship_cloakbrowser.cli import app


runner = CliRunner()


def test_root_help_explains_static_token_auth():
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "CLOAKBROWSER_URL" in result.stdout
    assert "CLOAKBROWSER_TOKEN" in result.stdout
    assert "AUTH_TOKEN" in result.stdout
    assert "static" in result.stdout.lower()


def test_list_profiles(monkeypatch):
    mock_profiles = [
        {
            "id": "profile-1",
            "name": "test-profile",
            "status": "running",
            "vnc_ws_port": 6080,
            "cdp_url": "/api/profiles/profile-1/cdp",
        }
    ]

    mock_client = MagicMock()
    mock_client.list_profiles.return_value = mock_profiles
    monkeypatch.setattr("ghostship_cloakbrowser.cli.get_client", lambda: mock_client)

    result = runner.invoke(app, ["list"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert len(payload) == 1
    assert payload[0]["name"] == "test-profile"
    assert payload[0]["status"] == "running"


def test_get_profile(monkeypatch):
    mock_profile = {
        "id": "profile-1",
        "name": "test-profile",
        "status": "running",
        "fingerprint_seed": 12345,
    }

    mock_client = MagicMock()
    mock_client.get_profile.return_value = mock_profile
    monkeypatch.setattr("ghostship_cloakbrowser.cli.get_client", lambda: mock_client)

    result = runner.invoke(app, ["get", "profile-1"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["id"] == "profile-1"


def test_create_profile(monkeypatch):
    mock_profile = {
        "id": "new-profile-id",
        "name": "my-new-profile",
        "status": "stopped",
    }

    mock_client = MagicMock()
    mock_client.create_profile.return_value = mock_profile
    monkeypatch.setattr("ghostship_cloakbrowser.cli.get_client", lambda: mock_client)

    result = runner.invoke(app, ["create", "my-new-profile"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["name"] == "my-new-profile"


def test_launch_profile(monkeypatch):
    mock_launch = {
        "profile_id": "profile-1",
        "status": "running",
        "vnc_ws_port": 6080,
        "display": ":1",
        "cdp_url": "/api/profiles/profile-1/cdp",
    }

    mock_client = MagicMock()
    mock_client.launch_profile.return_value = mock_launch
    monkeypatch.setattr("ghostship_cloakbrowser.cli.get_client", lambda: mock_client)

    result = runner.invoke(app, ["launch", "profile-1"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["status"] == "running"
    assert payload["cdp_url"] == "/api/profiles/profile-1/cdp"


def test_stop_profile(monkeypatch):
    mock_client = MagicMock()
    mock_client.stop_profile.return_value = True
    monkeypatch.setattr("ghostship_cloakbrowser.cli.get_client", lambda: mock_client)

    result = runner.invoke(app, ["stop", "profile-1"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["ok"] is True


def test_delete_profile(monkeypatch):
    mock_client = MagicMock()
    mock_client.delete_profile.return_value = True
    monkeypatch.setattr("ghostship_cloakbrowser.cli.get_client", lambda: mock_client)

    result = runner.invoke(app, ["delete", "profile-1"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["ok"] is True


def test_status(monkeypatch):
    mock_status = {
        "running_count": 2,
        "binary_version": "1.2.3",
        "profiles_total": 5,
    }

    mock_client = MagicMock()
    mock_client.get_system_status.return_value = mock_status
    monkeypatch.setattr("ghostship_cloakbrowser.cli.get_client", lambda: mock_client)

    result = runner.invoke(app, ["status"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["running_count"] == 2


def test_clipboard_get(monkeypatch):
    mock_clipboard = {"text": "copied text"}

    mock_client = MagicMock()
    mock_client.get_clipboard.return_value = mock_clipboard
    monkeypatch.setattr("ghostship_cloakbrowser.cli.get_client", lambda: mock_client)

    result = runner.invoke(app, ["clipboard-get", "profile-1"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["text"] == "copied text"


def test_clipboard_set(monkeypatch):
    mock_client = MagicMock()
    mock_client.set_clipboard.return_value = True
    monkeypatch.setattr("ghostship_cloakbrowser.cli.get_client", lambda: mock_client)

    result = runner.invoke(app, ["clipboard-set", "profile-1", "hello"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["ok"] is True


def test_cdp_info(monkeypatch):
    mock_cdp = {
        "cdp_url": "/api/profiles/profile-1/cdp",
        "usage": "playwright.chromium.connect_over_cdp('http://<host>/api/profiles/profile-1/cdp')",
    }

    mock_client = MagicMock()
    mock_client.get_cdp_info.return_value = mock_cdp
    monkeypatch.setattr("ghostship_cloakbrowser.cli.get_client", lambda: mock_client)

    result = runner.invoke(app, ["cdp-info", "profile-1"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert "playwright" in payload["usage"]
