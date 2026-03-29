import json
import pytest
from unittest.mock import patch, MagicMock
from typer.testing import CliRunner
from ghostship_onyx.cli import app

runner = CliRunner()

@pytest.fixture
def mock_env():
    with patch.dict("os.environ", {"ONYX_URL": "http://localhost:8080", "ONYX_API_KEY": "test-api-key"}):
        yield

@pytest.fixture
def mock_client():
    with patch("ghostship_onyx.cli.OnyxClient") as mock:
        yield mock.return_value

def test_ingest(mock_env, mock_client):
    mock_client.ingest_document.return_value = {"status": "success"}
    
    result = runner.invoke(app, ["ingest", "test-id", "hello text", "--source", "web", "--metadata", '{"key": "val"}'])
    
    assert result.exit_code == 0
    assert "success" in result.stdout
    mock_client.ingest_document.assert_called_once()
    args, kwargs = mock_client.ingest_document.call_args
    assert args[0]["semantic_identifier"] == "test-id"
    assert args[0]["sections"][0]["text"] == "hello text"
    assert args[0]["source"] == "web"
    assert args[0]["metadata"] == {"key": "val"}

def test_chat(mock_env, mock_client):
    mock_client.send_chat_message.return_value = {"message": "reply"}
    
    result = runner.invoke(app, ["chat", "hello", "--session-id", "session1", "--persona-id", "1"])
    
    assert result.exit_code == 0
    assert "reply" in result.stdout
    mock_client.send_chat_message.assert_called_once_with(message="hello", chat_session_id="session1", chat_session_info={"persona_id": 1})

def test_search_semantic(mock_env, mock_client):
    mock_client.semantic_search.return_value = {"results": []}
    
    result = runner.invoke(app, ["search", "test query"])
    
    assert result.exit_code == 0
    assert "results" in result.stdout
    mock_client.semantic_search.assert_called_once_with("test query")

def test_search_keyword(mock_env, mock_client):
    mock_client.keyword_search.return_value = {"results": []}
    
    result = runner.invoke(app, ["search", "test query", "--keyword"])
    
    assert result.exit_code == 0
    assert "results" in result.stdout
    mock_client.keyword_search.assert_called_once_with("test query")

def test_sessions(mock_env, mock_client):
    mock_client.get_chat_sessions.return_value = []
    
    result = runner.invoke(app, ["sessions"])
    
    assert result.exit_code == 0
    assert "[]" in result.stdout
    mock_client.get_chat_sessions.assert_called_once()

def test_missing_env():
    with patch.dict("os.environ", clear=True):
        result = runner.invoke(app, ["sessions"])
        assert result.exit_code == 1
        assert "Error: ONYX_URL and ONYX_API_KEY environment variables must be set." in result.stderr
