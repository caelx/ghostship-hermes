---
name: sonarr
description: Operate Sonarr from the Hermes image with `ghostship-sonarr`. Use when diagnosing Sonarr health, queue, history, or wanted-state issues; looking up or adding series; updating or deleting series; or running Sonarr commands through exact snake_case CLI operations.
---

# Sonarr Skill

Use `ghostship-sonarr` for Sonarr workflows that move from inspection to mutation to verification.

## Prerequisites

- `SONARR_URL`
- `SONARR_API_KEY`

## Operating Model

- Prefer dedicated snake_case commands first.
- Use `request` only for uncovered endpoints.
- Every command accepts `--timeout`; default hard timeout is `30` seconds.
- Write and delete operations support `--dry-run`.

## Start Here

- Health or connectivity: `ghostship-sonarr get_status`
- Current library state: `ghostship-sonarr get_series`
- Add flow: `ghostship-sonarr lookup_series`
- Import or backlog diagnosis: `ghostship-sonarr get_queue`, `ghostship-sonarr get_history`, `ghostship-sonarr get_wanted_missing`

## Common Workflows

- Add a series:
  - `lookup_series "<title>"` to find the exact match.
  - `get_root_folders` and `get_quality_profiles` before choosing IDs.
  - `add_series --dry-run ...`, then `add_series ...`.
  - `get_series` or `get_queue` to verify post-state.
- Diagnose missing or stuck episodes:
  - `get_wanted_missing`
  - `get_queue`
  - `get_history`
  - `get_blocklist` or `get_blocklist_series` if releases are repeatedly rejected.
- Trigger background work:
  - `get_commands` to see what Sonarr already supports.
  - `run_command ...` only after confirming the command name and intent.

## Mutation Guardrails

- Confirm series, root-folder, and quality-profile IDs before mutating.
- Use `--dry-run` for `add_series`, `update_series`, and `delete_series`.
- Re-read series, queue, or history state after every meaningful change.

## Fallback

- Use `ghostship-sonarr request` only when a dedicated command does not exist.
