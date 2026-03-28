---
name: searxng
description: Use the ghostship-searxng CLI to query the configured SearXNG instance with machine-readable output.
---

# SearXNG Skill

Use `ghostship-searxng` instead of direct HTTP calls when the CLI is available.

## Rules

- Prefer `ghostship-searxng search web "<query>" --json`
- Pass `--base-url` when the runtime does not provide `SEARXNG_BASE_URL`
- Use `--limit` to control result count
- Keep output machine-readable with `--json` when another tool or agent will consume it
