---
name: radarr
description: Operate Radarr from the Hermes image with `ghostship-radarr`. Use when diagnosing Radarr health, queue, history, wanted, or blocklist issues; looking up or adding movies; updating or deleting movies; or running Radarr commands through exact snake_case CLI operations.
---

# Radarr Skill

Use `ghostship-radarr` for Radarr workflows that inspect movie state first, then mutate and verify.

## Prerequisites

- `RADARR_URL`
- `RADARR_API_KEY`

## Operating Model

- Prefer dedicated snake_case commands first.
- Use `request` only for uncovered endpoints.
- Every command accepts `--timeout`; default hard timeout is `30` seconds.
- Write and delete operations support `--dry-run`.

## Start Here

- Health or connectivity: `ghostship-radarr get_status`
- Current movie library: `ghostship-radarr get_movies`
- Add flow: `ghostship-radarr lookup_movie`
- Missing or import diagnosis: `ghostship-radarr get_queue`, `ghostship-radarr get_history`, `ghostship-radarr get_wanted_missing`

## Common Workflows

- Add a movie:
  - `lookup_movie "<title>"` to find the correct record.
  - `get_root_folders` and `get_quality_profiles` before selecting IDs.
  - `add_movie --dry-run ...`, then `add_movie ...`.
  - `get_movies` or `get_queue` to verify the result.
- Diagnose missing or rejected movies:
  - `get_wanted_missing`
  - `get_wanted_cutoff`
  - `get_queue`
  - `get_history`
  - `get_blocklist` or `get_blocklist_movie` for rejection patterns.
- Trigger background work:
  - `get_commands`
  - `run_command ...` after confirming the correct command name.

## Mutation Guardrails

- Confirm movie, root-folder, tag, and quality-profile IDs before mutating.
- Use `--dry-run` for `add_movie`, `update_movie`, and `delete_movie`.
- Re-read library or queue state after every mutation.

## Fallback

- Use `ghostship-radarr request` only for uncovered endpoints.
