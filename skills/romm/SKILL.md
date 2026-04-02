---
name: romm
description: Operate RomM from the Hermes image with `ghostship-romm`. Use when checking heartbeat, libraries, platforms, ROMs, saves, scans, collections, config, or user state, or when updating ROM metadata or starting scans through exact snake_case CLI operations.
---

# RomM Skill

Use `ghostship-romm` for ROM library workflows that start with library inspection, then move into metadata or scan actions.

## Prerequisites

- `ROMM_URL`
- `ROMM_TOKEN` or `ROMM_USERNAME` and `ROMM_PASSWORD`

## Operating Model

- Prefer dedicated snake_case commands first.
- Use `request` only for uncovered endpoints.
- Every command accepts `--timeout`; default hard timeout is `30` seconds.
- Write and delete operations support `--dry-run`.

## Start Here

- Health or auth check: `ghostship-romm get_heartbeat`, `ghostship-romm get_user_me`
- Platform and library state: `ghostship-romm get_platforms`, `ghostship-romm get_libraries`
- ROM inspection: `ghostship-romm get_roms`
- Scan state: `ghostship-romm get_scans`

## Common Workflows

- Inspect a library:
  - `get_platforms`
  - `get_libraries`
  - `get_roms`
  - `get_rom <id>` for a specific title.
- Diagnose scan or import state:
  - `get_scans`
  - `get_config`
  - `get_collections` if the issue looks organization-related rather than scan-related.
- Update ROM metadata:
  - `get_rom <id>`
  - `update_rom --dry-run ...`, then `update_rom ...`
  - `get_rom <id>` again to verify.
- Start a scan:
  - Inspect current scan state first.
  - `start_scan`
  - Re-read `get_scans` to confirm the task was accepted.

## Mutation Guardrails

- Confirm ROM identifiers and current metadata before updating or deleting.
- Use `--dry-run` for `update_rom` and `delete_rom`.
- Re-read ROM or scan state after every mutation.

## Fallback

- Use `ghostship-romm request` only for uncovered endpoints.
