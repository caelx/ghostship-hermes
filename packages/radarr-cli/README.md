# ghostship-radarr

`ghostship-radarr` is a JSON-first CLI for its service API. Commands mirror the client/API method names exactly. No compatibility aliases are provided.

## Environment
- `RADARR_URL`
- `RADARR_API_KEY`

## Command Contract
- Primary commands use the exact snake_case client method names.
- Use `request` only for endpoints that are not covered by a dedicated wrapper yet.
- Output is JSON by default.

## Commands
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
