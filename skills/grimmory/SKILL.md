---
name: grimmory
description: Operate Grimmory from the Hermes image with `ghostship-grimmory`. Use when checking books, libraries, shelves, authors, tasks, or version state, or when scanning or refreshing libraries and cancelling tasks through exact snake_case CLI operations.
---

# Grimmory Skill

Use `ghostship-grimmory` for book-library workflows that move from inspection to library maintenance actions.

## Prerequisites

- `GRIMMORY_URL`
- `GRIMMORY_TOKEN` or `GRIMMORY_USERNAME` and `GRIMMORY_PASSWORD`

## Operating Model

- Prefer dedicated snake_case commands first.
- Use `request` only for uncovered endpoints.
- Every command accepts `--timeout`; default hard timeout is `30` seconds.
- Write and delete operations support `--dry-run`.
- Grimmory is more stable when a bearer token is reused for the session instead of re-authing on every call.

## Start Here

- Version or connectivity: `ghostship-grimmory get_version`
- Library inventory: `ghostship-grimmory get_libraries`, `ghostship-grimmory get_books`
- Task state: `ghostship-grimmory get_tasks`
- Shelf or author inspection: `ghostship-grimmory get_shelves`, `ghostship-grimmory get_authors`

## Common Workflows

- Inspect a library:
  - `get_libraries`
  - `get_library <id>`
  - `get_books`
  - `get_book <id>` as needed.
- Diagnose maintenance work:
  - `get_tasks`
  - `get_library <id>`
  - `get_version` if behavior looks instance-specific.
- Scan or refresh a library:
  - Inspect the library first.
  - `scan_libraries --dry-run ...` or `refresh_library --dry-run ...` if supported, then execute.
  - Re-read `get_tasks` or library state to confirm.
- Cancel a task:
  - Inspect `get_tasks` first.
  - Confirm the target task and whether cancellation is actually required.
  - `cancel_task --dry-run ...` if supported, then execute.

## Mutation Guardrails

- Confirm library or task IDs before acting.
- Prefer reading task state before launching new maintenance work.
- Re-read task or library state after every maintenance action.

## Fallback

- Use `ghostship-grimmory request` only for uncovered endpoints.
