from typing import Any, Dict, List, Optional
import httpx

class OnyxClient:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip("/")
        if not self.base_url.endswith("/api"):
            self.base_url = f"{self.base_url}/api"
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def _request(self, path: str, method: str = "GET", params: Optional[Dict[str, Any]] = None, json_data: Optional[Dict[str, Any]] = None) -> Any:
        url = f"{self.base_url}/{path.lstrip('/')}"
        with httpx.Client(headers=self.headers) as client:
            if method == "POST":
                response = client.post(url, json=json_data, params=params)
            elif method == "DELETE":
                response = client.delete(url, params=params)
            elif method == "PATCH":
                response = client.patch(url, json=json_data, params=params)
            else:
                response = client.get(url, params=params)
            
            response.raise_for_status()
            if not response.content:
                return {"status": "success"}
            return response.json()

    # Ingestion API
    def ingest_document(self, document: Dict[str, Any], cc_pair_id: Optional[int] = None) -> Any:
        payload = {"document": document}
        if cc_pair_id is not None:
            payload["cc_pair_id"] = cc_pair_id
        return self._request("onyx-api/ingestion", method="POST", json_data=payload)

    def delete_document(self, doc_id: str) -> Any:
        return self._request(f"onyx-api/ingestion/{doc_id}", method="DELETE")

    # Chat API
    def send_chat_message(self, message: str, chat_session_id: Optional[str] = None, stream: bool = False, **kwargs) -> Any:
        payload = {
            "message": message,
            "chat_session_id": chat_session_id,
            "stream": stream,
            **kwargs
        }
        return self._request("chat/send-chat-message", method="POST", json_data=payload)

    def get_chat_sessions(self) -> Any:
        return self._request("chat/get-user-chat-sessions")

    def get_chat_history(self, chat_session_id: str) -> Any:
        return self._request(f"chat/get-chat-session-history", params={"chat_session_id": chat_session_id})

    # Search API
    def semantic_search(self, query: str, **kwargs) -> Any:
        payload = {"query": query, **kwargs}
        return self._request("search/semantic-search", method="POST", json_data=payload)

    def keyword_search(self, query: str, **kwargs) -> Any:
        payload = {"query": query, **kwargs}
        return self._request("search/keyword-search", method="POST", json_data=payload)
