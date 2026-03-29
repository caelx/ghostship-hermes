from typer.testing import CliRunner
from ghostship_flaresolverr.cli import app
from unittest.mock import patch, MagicMock
import json

runner = CliRunner()

@patch("ghostship_flaresolverr.cli.FlareSolverrClient")
def test_get(mock_client_class):
    mock_client = MagicMock()
    mock_client_class.return_value = mock_client
    mock_client.request_get.return_value = {"status": "ok", "solution": {"response": "html"}}

    result = runner.invoke(app, ["get", "https://example.com"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["status"] == "ok"
    mock_client.request_get.assert_called_once_with("https://example.com", session=None)

@patch("ghostship_flaresolverr.cli.FlareSolverrClient")
def test_list_sessions(mock_client_class):
    mock_client = MagicMock()
    mock_client_class.return_value = mock_client
    mock_client.sessions_list.return_value = {"status": "ok", "sessions": ["session1"]}

    result = runner.invoke(app, ["list-sessions"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "sessions" in data
    assert data["sessions"] == ["session1"]
