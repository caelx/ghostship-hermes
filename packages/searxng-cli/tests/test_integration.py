import json
import os

import pytest
from typer.testing import CliRunner

from ghostship_searxng.cli import app


runner = CliRunner()


@pytest.mark.integration
def test_live_searxng_query():
    base_url = os.getenv("SEARXNG_BASE_URL")
    if not base_url:
        pytest.skip("Set SEARXNG_BASE_URL to run integration tests.")

    result = runner.invoke(app, ["search", "web", "ghostship hermes", "--base-url", base_url, "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert "results" in payload
