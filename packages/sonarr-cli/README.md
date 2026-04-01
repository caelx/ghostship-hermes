# ghostship-sonarr

`ghostship-sonarr` is a JSON-first CLI for its service API. Commands mirror the client/API method names exactly. No compatibility aliases are provided.

## Environment
- `SONARR_URL`
- `SONARR_API_KEY`

## Command Contract
- Primary commands use the exact snake_case client method names.
- Use `request` only for endpoints that are not covered by a dedicated wrapper yet.
- Output is JSON by default.
- Every invocation accepts `--timeout`; the default hard timeout is `30` seconds.
- Where a service exposes write or delete operations, those commands accept `--dry-run` and print the exact request object instead of calling the API.

## Commands
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
