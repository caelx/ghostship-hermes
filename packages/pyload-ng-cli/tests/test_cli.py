from typer.testing import CliRunner
import json
from ghostship_pyload_ng.cli import app

runner = CliRunner()

def test_status_no_env():
    result = runner.invoke(app, ["status"])
    assert result.exit_code == 1
    assert "Error: PYLOAD_URL, PYLOAD_USER, and PYLOAD_PASS environment variables must be set." in result.stderr
