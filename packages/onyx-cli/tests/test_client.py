import unittest
from unittest.mock import patch, MagicMock
from ghostship_onyx.client import OnyxClient
import httpx

class TestOnyxClient(unittest.TestCase):
    def setUp(self):
        self.base_url = "http://localhost:8080"
        self.api_key = "test-api-key"
        self.client = OnyxClient(self.base_url, self.api_key)

    @patch("httpx.Client.request")
    def test_request_get(self, mock_request):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"key": "value"}
        mock_response.content = b'{"key": "value"}'
        mock_request.return_value = mock_response

        # Need to patch the specific methods because they are called on the instance inside _request
        with patch("httpx.Client.get") as mock_get:
            mock_get.return_value = mock_response
            result = self.client._request("test-path")
            mock_get.assert_called_once_with(f"{self.base_url}/api/test-path", params=None)
            self.assertEqual(result, {"key": "value"})

    @patch("httpx.Client.post")
    def test_ingest_document(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "success"}
        mock_response.content = b'{"status": "success"}'
        mock_post.return_value = mock_response

        document = {"id": "doc1", "text": "hello"}
        result = self.client.ingest_document(document)
        
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertEqual(args[0], f"{self.base_url}/api/onyx-api/ingestion")
        self.assertEqual(kwargs["json"], {"document": document})
        self.assertEqual(result, {"status": "success"})

    @patch("httpx.Client.delete")
    def test_delete_document(self, mock_delete):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"" # empty content means it returns {"status": "success"}
        mock_delete.return_value = mock_response

        result = self.client.delete_document("doc1")
        
        mock_delete.assert_called_once_with(f"{self.base_url}/api/onyx-api/ingestion/doc1", params=None)
        self.assertEqual(result, {"status": "success"})

    @patch("httpx.Client.post")
    def test_send_chat_message(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"message": "reply"}
        mock_response.content = b'{"message": "reply"}'
        mock_post.return_value = mock_response

        result = self.client.send_chat_message("hello")
        
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertEqual(args[0], f"{self.base_url}/api/chat/send-chat-message")
        self.assertEqual(kwargs["json"]["message"], "hello")
        self.assertEqual(result, {"message": "reply"})

    @patch("httpx.Client.get")
    def test_get_chat_sessions(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        mock_response.content = b"[]"
        mock_get.return_value = mock_response

        result = self.client.get_chat_sessions()
        
        mock_get.assert_called_once_with(f"{self.base_url}/api/chat/get-user-chat-sessions", params=None)
        self.assertEqual(result, [])

    @patch("httpx.Client.get")
    def test_get_chat_history(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"history": []}
        mock_response.content = b'{"history": []}'
        mock_get.return_value = mock_response

        result = self.client.get_chat_history("session1")
        
        mock_get.assert_called_once_with(f"{self.base_url}/api/chat/get-chat-session-history", params={"chat_session_id": "session1"})
        self.assertEqual(result, {"history": []})

    @patch("httpx.Client.post")
    def test_semantic_search(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"results": []}
        mock_response.content = b'{"results": []}'
        mock_post.return_value = mock_response

        result = self.client.semantic_search("test")
        
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertEqual(args[0], f"{self.base_url}/api/search/semantic-search")
        self.assertEqual(kwargs["json"]["query"], "test")
        self.assertEqual(result, {"results": []})

    @patch("httpx.Client.post")
    def test_keyword_search(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"results": []}
        mock_response.content = b'{"results": []}'
        mock_post.return_value = mock_response

        result = self.client.keyword_search("test")
        
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertEqual(args[0], f"{self.base_url}/api/search/keyword-search")
        self.assertEqual(kwargs["json"]["query"], "test")
        self.assertEqual(result, {"results": []})

if __name__ == "__main__":
    unittest.main()
