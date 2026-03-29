---
name: onyx
description: Manage RAG ingestion and chat via Onyx. Output is native JSON.
---

# Onyx Skill

The `ghostship-onyx` utility allows agents to manage a persistent knowledge base (RAG) and interact with chat sessions via the Onyx API.

## Structure

- **Skill Document:** `skills/onyx/SKILL.md` (this file)
- **Package Directory:** `packages/onyx-cli/`
- **README:** `packages/onyx-cli/README.md`

## Prerequisites

The following environment variables must be configured:
- `ONYX_URL`: The base URL of the Onyx instance.
- `ONYX_API_KEY`: Your Onyx API key or Personal Access Token.

## Usage

All commands output native JSON.

### Commands

#### `ghostship-onyx ingest <identifier> <text>`
Ingest a document for RAG.
- `identifier`: A semantic name for the document (e.g., filename or title).
- `text`: The content to index.
- `--cc-pair-id`: Optional ID of the connector/credential pair to associate with.
- `--source`: Source type (default: `file`).
- `--metadata`: Optional JSON string of metadata.

#### `ghostship-onyx chat "<message>"`
Send a message to an Onyx chat session.
- `--session-id`: Optional ID of an existing session to continue.
- `--persona-id`: Optional ID of the agent persona to use.

#### `ghostship-onyx search "<query>"`
Perform a semantic or keyword search across indexed documents.
- `--keyword`: Use keyword search instead of semantic search.

#### `ghostship-onyx delete <doc_id>`
Permanently remove a document from the index.

#### `ghostship-onyx history <session_id>`
Retrieve the full message history for a specific chat session.

#### `ghostship-onyx sessions`
List available chat sessions for the user.

## Examples

```bash
# Ingest a project README
ghostship-onyx ingest "README.md" "$(cat README.md)" --source "github"

# Ask Onyx about the ingested content
ghostship-onyx chat "What is ghostship-hermes?" --pretty

# Delete a stale document
ghostship-onyx delete "doc_123"
```

## Agent Guidance

- Use `ingest` to store long-term information that Hermes should remember across sessions.
- Use `search` to retrieve relevant context from the knowledge base when answering user questions.
- Prefer `chat` for complex reasoning over indexed documents.
- Use `history` to retrieve past context from a conversation if needed.
- Always handle the JSON output, which contains the results of the operation or any errors.
