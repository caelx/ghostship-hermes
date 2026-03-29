from typer.testing import CliRunner
import json
from ghostship_nzbget.cli import app

runner = CliRunner()

def test_info():
    result = runner.invoke(app, ["info", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["api"] == "Nzbget"
