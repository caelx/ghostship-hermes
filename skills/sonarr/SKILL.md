---
name: sonarr
description: Use when you need Sonarr series, episode, queue, or command endpoints through exact method-name commands.
---

# ghostship-sonarr

- Commands mirror the API/client method names exactly. Do not guess aliases.
- Configure the utility with:
- `SONARR_URL`
- `SONARR_API_KEY`
- Prefer the dedicated snake_case command first. Use `request` only as fallback.

## Common Commands
- `ghostship-sonarr request`
- `ghostship-sonarr get_status`
- `ghostship-sonarr get_series`
- `ghostship-sonarr lookup_series`
- `ghostship-sonarr add_series`
- `ghostship-sonarr update_series`
- `ghostship-sonarr delete_series`
- `ghostship-sonarr get_episodes`
- `ghostship-sonarr get_episode`
- `ghostship-sonarr update_episode`
- `ghostship-sonarr get_commands`
- `ghostship-sonarr run_command`
- `ghostship-sonarr get_queue`
- `ghostship-sonarr get_history`
- `ghostship-sonarr get_wanted_missing`
- `ghostship-sonarr get_wanted_cutoff`
- `ghostship-sonarr get_blocklist`
- `ghostship-sonarr get_blocklist_series`
- `ghostship-sonarr get_tags`
- `ghostship-sonarr get_root_folders`
- `ghostship-sonarr get_quality_profiles`

## Examples
```bash
ghostship-sonarr get_status --pretty
```
```bash
ghostship-sonarr lookup_series "the office" --pretty
```
```bash
ghostship-sonarr get_series --pretty
```
