---
name: tautulli
description: Operate Tautulli from the Hermes image with `ghostship-tautulli`. Use when checking server health, activity, history, libraries, users, metadata, or when terminating sessions or restarting Tautulli through exact snake_case CLI operations.
---

# Tautulli Skill

Use `ghostship-tautulli` for Plex monitoring and operator workflows that are usually read-heavy with occasional targeted control actions.

## Prerequisites

- `TAUTULLI_URL`
- `TAUTULLI_API_KEY`

## Operating Model

- Prefer dedicated snake_case commands first.
- Use `call` only for uncovered endpoints.
- Every command accepts `--timeout`; default hard timeout is `30` seconds.
- Write-like actions support `--dry-run` where the CLI exposes them.

## Start Here

- System and API state: `ghostship-tautulli get_server_status`, `ghostship-tautulli get_tautulli_info`, `ghostship-tautulli get_status`
- Live playback: `ghostship-tautulli get_activity`
- Historical diagnosis: `ghostship-tautulli get_history`
- User or library analysis: `ghostship-tautulli get_users`, `ghostship-tautulli get_libraries`

## Common Workflows

- Diagnose playback issues:
  - `get_activity`
  - `get_history`
  - `get_metadata <rating-key>` for the affected item if needed.
- Inspect user behavior:
  - `get_users`
  - `get_user_player_stats`
  - `get_user_watch_time_stats`
- Review library behavior:
  - `get_libraries`
  - `get_library_user_stats`
- Terminate a problematic session:
  - Inspect `get_activity` first.
  - Confirm the session target.
  - `terminate_session --dry-run ...` if supported, then execute.
  - Re-read `get_activity` to verify.
- Restart Tautulli:
  - Use only after confirming the problem is server-side rather than data-side.
  - Re-read `get_status` or `get_tautulli_info` after restart.

## Mutation Guardrails

- Treat `terminate_session` and `restart` as explicit operator actions, not first-line diagnostics.
- Confirm the live session or server issue with read commands before acting.
- Re-read system or activity state after control actions.

## Fallback

- Use `ghostship-tautulli call` only for uncovered endpoints.
