---
name: bazarr
description: Use when you need subtitle and system data from Bazarr via exact API/client method names.
---

# ghostship-bazarr

- Commands mirror the API/client method names exactly. Do not guess aliases.
- Every invocation accepts `--timeout`; default hard timeout is `30` seconds.
- Where the service exposes write/delete operations, those commands support `--dry-run` and print the exact request object without calling the API.
- Configure the utility with:
- `BAZARR_URL`
- `BAZARR_API_KEY`
- Prefer the dedicated snake_case command first. Use `request` only as fallback.

## Common Commands
- `ghostship-bazarr request`
- `ghostship-bazarr get_badges`
- `ghostship-bazarr get_episodes`
- `ghostship-bazarr get_wanted_episodes`
- `ghostship-bazarr get_movies`
- `ghostship-bazarr get_wanted_movies`
- `ghostship-bazarr get_series`
- `ghostship-bazarr get_providers`
- `ghostship-bazarr get_subtitles`
- `ghostship-bazarr get_system_health`
- `ghostship-bazarr get_system_jobs`
- `ghostship-bazarr get_system_tasks`
- `ghostship-bazarr get_system_status`
- `ghostship-bazarr search_subtitles_missing`
- `ghostship-bazarr get_episodes_history`
- `ghostship-bazarr get_movies_history`
- `ghostship-bazarr get_episodes_blacklist`
- `ghostship-bazarr get_movies_blacklist`

## Examples
```bash
ghostship-bazarr get_system_status --pretty
```
```bash
ghostship-bazarr get_episodes --series-id 123 --pretty
```
```bash
ghostship-bazarr request GET system/status
```
