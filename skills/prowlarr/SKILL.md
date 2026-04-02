---
name: prowlarr
description: Operate Prowlarr from the Hermes image with `ghostship-prowlarr`. Use when inspecting indexers, applications, history, indexer health, or running searches and commands through exact snake_case CLI operations.
---

# Prowlarr Skill

Use `ghostship-prowlarr` for indexer operations that start with health and configuration state, then move into search or command execution.

## Prerequisites

- `PROWLARR_URL`
- `PROWLARR_API_KEY`

## Operating Model

- Prefer dedicated snake_case commands first.
- Use `request` only for uncovered endpoints.
- Every command accepts `--timeout`; default hard timeout is `30` seconds.
- Where supported, write or delete operations expose `--dry-run`.

## Start Here

- System health: `ghostship-prowlarr get_status`
- Indexer inventory: `ghostship-prowlarr get_indexers`
- Application wiring: `ghostship-prowlarr get_applications`
- Search or failure diagnosis: `ghostship-prowlarr get_history`, `ghostship-prowlarr get_indexer_status`

## Common Workflows

- Diagnose search failures:
  - `get_indexers`
  - `get_indexer_status`
  - `get_history`
  - `search "<query>"` after confirming indexers are healthy.
- Check app synchronization state:
  - `get_applications`
  - `run_command ...` only after confirming the intended sync or maintenance action.
- Review indexer performance:
  - `get_indexer_stats`
  - `get_indexer_status`

## Mutation Guardrails

- Inspect indexer and application state before running commands.
- Treat `run_command` as an explicit operator action, not a first diagnostic step.
- Re-read status or history after any command execution that should change system state.

## Fallback

- Use `ghostship-prowlarr request` only for uncovered endpoints.
