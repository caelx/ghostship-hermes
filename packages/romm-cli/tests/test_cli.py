from typer.testing import CliRunner

from ghostship_romm.cli import app


runner = CliRunner()


def test_root_help_explains_auth_flow():
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "ROMM_URL" in result.stdout
    assert "ROMM_USERNAME" in result.stdout
    assert "ROMM_PASSWORD" in result.stdout
    assert "ROMM_TOKEN" in result.stdout
    assert "/api/token" in result.stdout
