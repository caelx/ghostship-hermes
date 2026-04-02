---
name: searxng
description: Search through the Hermes image with `ghostship-searxng`. Use when you need web results from the configured SearXNG instance, want to tune engines and limits for a query, or need raw endpoint access for search parameters not covered by the typed command.
---

# SearXNG Skill

Use `ghostship-searxng` when you need metasearch results from the configured SearXNG instance.

## Prerequisites

- `SEARXNG_URL`

## Operating Model

- Prefer dedicated snake_case commands first.
- Use `request` only for uncovered endpoint parameters.
- Every command accepts `--timeout`; default hard timeout is `30` seconds.
- This is primarily a read workflow: choose the narrowest query and engine mix that answers the task.

## Start Here

- Normal search flow: `ghostship-searxng search web "<query>"`
- Raw endpoint access: `ghostship-searxng request search --param q=<query> --param format=json`

## Common Workflows

- Run a targeted search:
  - `search web "<query>" --limit <n>` first.
  - Refine with engine, language, or pagination flags rather than broadening the query immediately.
  - Re-run the narrowed search until the result set is precise enough for the downstream task.
- Compare search configurations:
  - Run `search web` with the same query and different limit or engine options.
  - Use the JSON output to compare ranking and coverage before choosing a result set for another tool.
- Use raw request mode for uncovered options:
  - Start with a working `search web` query so you know the instance is reachable.
  - Switch to `request search --param ...` only for parameters the typed search command does not expose.
  - Keep `format=json` explicit in request mode so the output stays agent-friendly.

## Mutation Guardrails

- There are no normal write flows here; avoid `request` patterns that rely on undocumented non-search endpoints.
- Keep search queries scoped to the user’s need instead of scraping broadly by default.
- Verify the returned engines and payload shape before passing results into another automation step.

## Fallback

- Use `ghostship-searxng request` only when a dedicated search command does not exist for the needed parameter set.
