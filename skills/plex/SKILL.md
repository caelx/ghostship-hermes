---
name: plex
description: Operate Plex from the Hermes image with `ghostship-plex`. Use when checking server identity, libraries, metadata, sessions, activities, playlists, collections, or when refreshing libraries or terminating sessions through exact snake_case CLI operations.
---

# Plex Skill

Use `ghostship-plex` for Plex workflows that begin with server or library inspection and only then move into targeted actions.

## Prerequisites

- `PLEX_URL`
- `PLEX_TOKEN`

## Operating Model

- Prefer dedicated snake_case commands first.
- Use `request` only for uncovered endpoints.
- Every command accepts `--timeout`; default hard timeout is `30` seconds.
- Write-like actions support `--dry-run` where the CLI exposes them.

## Start Here

- Server identity: `ghostship-plex get_identity`, `ghostship-plex get_server_info`
- Active playback: `ghostship-plex get_status_sessions`, `ghostship-plex get_activities`
- Library inspection: `ghostship-plex get_library_sections`
- Metadata inspection: `ghostship-plex get_metadata`

## Common Workflows

- Inspect library state:
  - `get_library_sections`
  - `get_library_section <id>`
  - `get_library_filters <id>` or `get_library_sorts <id>` if you need the browsing shape.
- Investigate active playback:
  - `get_status_sessions`
  - `get_session <id>`
  - `get_activities`
- Refresh a library:
  - Inspect the section first.
  - `refresh_library --dry-run ...` if supported, then `refresh_library ...`.
  - Re-read section or activity state if the refresh should have visible effects.
- Terminate a session:
  - Inspect `get_status_sessions` first.
  - Confirm the target session with `get_session`.
  - `terminate_session --dry-run ...` if supported, then execute.
  - Re-read sessions to verify removal.

## Mutation Guardrails

- Confirm library section or session IDs before acting.
- Use read commands to confirm the target object exists and is the intended one.
- Re-read sessions, metadata, or library state after actions.

## Fallback

- Use `ghostship-plex request` only for uncovered endpoints.
