from typer.testing import CliRunner
import json
from ghostship_pyload_ng.cli import app

runner = CliRunner()

def test_status_no_env():
    result = runner.invoke(app, ["status"])
    assert result.exit_code == 1
    assert "Error: PYLOAD_URL environment variable must be set." in result.stderr



def test_status_url_only(monkeypatch):
    monkeypatch.setenv("PYLOAD_URL", "http://localhost:8000")
    monkeypatch.delenv("PYLOAD_USER", raising=False)
    monkeypatch.delenv("PYLOAD_PASS", raising=False)

    result = runner.invoke(app, ["status"])
    assert result.exit_code == 1
    assert "Error fetching status" in result.stderr
