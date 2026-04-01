---
name: radarr
description: Use when you need Radarr movie and queue endpoints via exact client method names.
---

# ghostship-radarr

- Commands mirror the API/client method names exactly. Do not guess aliases.
- Configure the utility with:
- `RADARR_URL`
- `RADARR_API_KEY`
- Prefer the dedicated snake_case command first. Use `request` only as fallback.

## Common Commands
- `ghostship-radarr request`
- `ghostship-radarr get_status`
- `ghostship-radarr get_movies`
- `ghostship-radarr lookup_movie`
- `ghostship-radarr add_movie`
- `ghostship-radarr update_movie`
- `ghostship-radarr delete_movie`
- `ghostship-radarr get_commands`
- `ghostship-radarr run_command`
- `ghostship-radarr get_queue`
- `ghostship-radarr get_history`
- `ghostship-radarr get_wanted_missing`
- `ghostship-radarr get_wanted_cutoff`
- `ghostship-radarr get_blocklist`
- `ghostship-radarr get_blocklist_movie`
- `ghostship-radarr get_tags`
- `ghostship-radarr get_root_folders`
- `ghostship-radarr get_quality_profiles`

## Examples
```bash
ghostship-radarr get_status --pretty
```
```bash
ghostship-radarr lookup_movie inception --pretty
```
```bash
ghostship-radarr get_movies --pretty
```
