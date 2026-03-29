from typer.testing import CliRunner
import json
from unittest.mock import patch, MagicMock
from ghostship_sonarr.cli import app

runner = CliRunner()

@patch("ghostship_sonarr.cli.SonarrClient")
@patch.dict("os.environ", {"SONARR_URL": "http://localhost:8989", "SONARR_API_KEY": "test_key"})
def test_info(mock_client):
    mock_instance = mock_client.return_value
    mock_instance.get_status.return_value = {"version": "3.0.0", "osName": "linux", "startupPath": "/app"}
    
    result = runner.invoke(app, ["info", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["version"] == "3.0.0"
