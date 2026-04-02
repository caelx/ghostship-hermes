---
name: bazarr
description: Operate Bazarr from the Hermes image with `ghostship-bazarr`. Use when checking subtitle health, wanted subtitles, providers, history, blacklist state, or when launching subtitle search workflows through exact snake_case CLI operations.
---

# Bazarr Skill

Use `ghostship-bazarr` for subtitle triage and search workflows around existing Sonarr or Radarr libraries.

## Prerequisites

- `BAZARR_URL`
- `BAZARR_API_KEY`

## Operating Model

- Prefer dedicated snake_case commands first.
- Use `request` only for uncovered endpoints.
- Every command accepts `--timeout`; default hard timeout is `30` seconds.
- Where supported, write or delete operations expose `--dry-run`.

## Start Here

- Overall health: `ghostship-bazarr get_system_status`
- Subtitle backlog: `ghostship-bazarr get_wanted_episodes`, `ghostship-bazarr get_wanted_movies`
- Provider readiness: `ghostship-bazarr get_providers`
- Search and rejection diagnosis: history and blacklist commands

## Common Workflows

- Diagnose missing subtitles:
  - `get_wanted_episodes` or `get_wanted_movies`
  - `get_providers`
  - `get_subtitles`
  - `get_system_health`
- Investigate repeated failures:
  - `get_episodes_history` or `get_movies_history`
  - `get_episodes_blacklist` or `get_movies_blacklist`
- Launch subtitle search:
  - Inspect the target episode or movie set first.
  - Run `search_subtitles_missing`.
  - Re-read wanted lists or subtitle state to confirm improvement.

## Mutation Guardrails

- Read provider and subtitle state before kicking off searches.
- Verify whether the issue is provider health, blacklist state, or missing media metadata before retrying searches.
- Re-check wanted queues and subtitle results after actions.

## Fallback

- Use `ghostship-bazarr request` only when no dedicated command exists.
