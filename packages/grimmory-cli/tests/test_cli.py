from typer.testing import CliRunner

from ghostship_grimmory.cli import app


runner = CliRunner()


def test_root_help_explains_auth_flow():
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "GRIMMORY_URL" in result.stdout
    assert "GRIMMORY_USERNAME" in result.stdout
    assert "GRIMMORY_PASSWORD" in result.stdout
    assert "GRIMMORY_TOKEN" in result.stdout
    assert "/api/v1/auth/login" in result.stdout
