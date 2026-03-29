# Ghostship-Onyx Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement a fully featured CLI utility for the Onyx API, with a focus on ingestion for RAG.

**Architecture:** Python CLI using Typer and httpx, following the ghostship-hermes Python utility conventions (JSON output, environment variables).

**Tech Stack:** Python 3.11+, Typer, httpx, pytest.

---

### Task 1: Package Scaffolding

**Files:**
- Create: `packages/onyx-cli/pyproject.toml`
- Create: `packages/onyx-cli/package.nix`
- Create: `packages/onyx-cli/README.md`
- Create: `packages/onyx-cli/src/ghostship_onyx/__init__.py`
- Create: `packages/onyx-cli/src/ghostship_onyx/py.typed`

- [ ] **Step 1: Create pyproject.toml**
```toml
[build-system]
requires = ["hatchling>=1.27.0"]
build-backend = "hatchling.build"

[project]
name = "ghostship-onyx"
version = "0.1.0"
description = "Onyx CLI wrapper for ghostship-hermes"
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
  "httpx>=0.28.1",
  "typer>=0.16.0",
]

[project.optional-dependencies]
dev = [
  "mypy>=1.18.2",
  "pytest>=8.4.2",
]

[project.scripts]
ghostship-onyx = "ghostship_onyx.cli:main"

[tool.pytest.ini_options]
addopts = "-ra"
testpaths = ["tests"]
```

- [ ] **Step 2: Create package.nix**
```nix
{ python311Packages }:
python311Packages.buildPythonApplication {
  pname = "ghostship-onyx";
  version = "0.1.0";
  pyproject = true;
  src = ./.;

  build-system = with python311Packages; [
    hatchling
  ];

  dependencies = with python311Packages; [
    httpx
    typer
  ];

  nativeCheckInputs = with python311Packages; [
    pytestCheckHook
  ];

  pythonImportsCheck = [ "ghostship_onyx" ];
}
```

- [ ] **Step 3: Create src directory structure**
```bash
mkdir -p packages/onyx-cli/src/ghostship_onyx
touch packages/onyx-cli/src/ghostship_onyx/__init__.py
touch packages/onyx-cli/src/ghostship_onyx/py.typed
```

---

### Task 2: Core API Client

**Files:**
- Create: `packages/onyx-cli/src/ghostship_onyx/client.py`

- [ ] **Step 1: Implement OnyxClient**
Include support for Ingestion, Chat, and Search.

```python
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
        # Verify path, usually /onyx-api/ingestion/{doc_id} or similar
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
```

---

### Task 3: CLI Endpoints

**Files:**
- Create: `packages/onyx-cli/src/ghostship_onyx/cli.py`

- [ ] **Step 1: Implement Typer CLI**
Standardize on native JSON output and `--pretty`.

```python
import typer
import os
import json
import sys
from typing import Optional, List, Any
from .client import OnyxClient

app = typer.Typer(help="Onyx CLI interface for RAG and Chat.")

def echo_json(data: Any, pretty: bool = False):
    indent = 2 if pretty else None
    typer.echo(json.dumps(data, indent=indent))

def get_client() -> OnyxClient:
    base_url = os.getenv("ONYX_URL")
    api_key = os.getenv("ONYX_API_KEY")
    if not base_url or not api_key:
        print("Error: ONYX_URL and ONYX_API_KEY environment variables must be set.", file=sys.stderr)
        raise typer.Exit(code=1)
    return OnyxClient(base_url, api_key)

@app.command()
def ingest(
    identifier: str,
    text: str,
    source: str = "file",
    cc_pair_id: Optional[int] = None,
    doc_id: Optional[str] = None,
    link: Optional[str] = None,
    metadata: Optional[str] = typer.Option(None, "--metadata", help="JSON string of metadata"),
    pretty: bool = typer.Option(False, "--pretty")
):
    """Ingest a document into Onyx."""
    client = get_client()
    try:
        meta_dict = json.loads(metadata) if metadata else {}
        document = {
            "id": doc_id,
            "semantic_identifier": identifier,
            "sections": [{"text": text, "link": link}],
            "source": source,
            "metadata": meta_dict
        }
        data = client.ingest_document(document, cc_pair_id=cc_pair_id)
        echo_json(data, pretty=pretty)
    except Exception as e:
        echo_json({"error": str(e)}, pretty=pretty)
        raise typer.Exit(code=1)

@app.command()
def chat(
    message: str,
    session_id: Optional[str] = None,
    persona_id: Optional[int] = None,
    pretty: bool = typer.Option(False, "--pretty")
):
    """Send a message to Onyx Chat."""
    client = get_client()
    try:
        kwargs = {}
        if persona_id:
            kwargs["chat_session_info"] = {"persona_id": persona_id}
        data = client.send_chat_message(message, chat_session_id=session_id, **kwargs)
        echo_json(data, pretty=pretty)
    except Exception as e:
        echo_json({"error": str(e)}, pretty=pretty)
        raise typer.Exit(code=1)

@app.command()
def search(query: str, keyword: bool = False, pretty: bool = typer.Option(False, "--pretty")):
    """Search documents in Onyx."""
    client = get_client()
    try:
        if keyword:
            data = client.keyword_search(query)
        else:
            data = client.semantic_search(query)
        echo_json(data, pretty=pretty)
    except Exception as e:
        echo_json({"error": str(e)}, pretty=pretty)
        raise typer.Exit(code=1)

@app.command()
def list_sessions(pretty: bool = typer.Option(False, "--pretty")):
    """List chat sessions."""
    client = get_client()
    try:
        data = client.get_chat_sessions()
        echo_json(data, pretty=pretty)
    except Exception as e:
        echo_json({"error": str(e)}, pretty=pretty)
        raise typer.Exit(code=1)

def main():
    app()
```

---

### Task 4: Skill and Integration

- [ ] **Step 1: Create skills/onyx/SKILL.md**
- [ ] **Step 2: Update flake.nix**
- [ ] **Step 3: Update packages/hermes-image/image.nix**
- [ ] **Step 4: Update docs/superpowers/specs/2026-03-28-ghostship-onyx-design.md**
