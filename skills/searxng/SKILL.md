---
name: searxng
description: Search the web via SearXNG. Output is native JSON.
---

# SearXNG Skill

The `ghostship-searxng` utility allows agents to perform web searches across multiple categories using a SearXNG instance.

## Prerequisites

The following environment variables must be configured:
- `SEARXNG_URL`: The base URL of the SearXNG instance (e.g., `http://localhost:8080`).

## Usage

All commands output native JSON. Use `--pretty` for human-readable output.

### Commands

#### `ghostship-searxng search web "<query>"`
Perform a web search.
- `query`: The search term.
- `--category`: The search category (default: `general`). Common categories: `general`, `images`, `news`, `science`, `it`.
- `--limit`: Number of results to return (default: `5`).
- `--language`: Language code (default: `all`).
- `--safe-search`: Safe search filter (0: Off, 1: Moderate, 2: Strict). Default: `1`.
- `--pretty`: Pretty print the JSON output.

## Examples

```bash
# Basic search
ghostship-searxng search web "nixos hermes"

# news search with limit
ghostship-searxng search web "current events" --category news --limit 3 --pretty
```

## Agent Guidance

- Use SearXNG to gather information from the internet when internal knowledge is insufficient.
- Prefer specific categories like `it` or `science` for technical queries to improve result relevance.
- Always handle the JSON response, which includes `query`, `number_of_results`, and a list of `results` with `title` and `url`.
