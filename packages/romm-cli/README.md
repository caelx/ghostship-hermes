# ghostship-romm

`ghostship-romm` is a JSON-first CLI for its service API. Commands mirror the client/API method names exactly. No compatibility aliases are provided.

## Environment
- `ROMM_URL`
- `ROMM_TOKEN or ROMM_USERNAME and ROMM_PASSWORD`

## Command Contract
- Primary commands use the exact snake_case client method names.
- Use `request` only for endpoints that are not covered by a dedicated wrapper yet.
- Output is JSON by default.
- Every invocation accepts `--timeout`; the default hard timeout is `30` seconds.
- Where a service exposes write or delete operations, those commands accept `--dry-run` and print the exact request object instead of calling the API.

## Commands
- `ghostship-romm request`
- `ghostship-romm get_heartbeat`
- `ghostship-romm get_platforms`
- `ghostship-romm get_libraries`
- `ghostship-romm get_roms`
- `ghostship-romm get_rom`
- `ghostship-romm update_rom`
- `ghostship-romm delete_rom`
- `ghostship-romm get_scans`
- `ghostship-romm start_scan`
- `ghostship-romm get_collections`
- `ghostship-romm get_config`
- `ghostship-romm get_saves`
- `ghostship-romm get_saves_summary`
- `ghostship-romm get_save`
- `ghostship-romm get_users`
- `ghostship-romm get_user_me`

## Examples
```bash
ghostship-romm get_heartbeat --pretty
```
```bash
ghostship-romm get_roms --page-size 5 --pretty
```
```bash
ghostship-romm get_collections --pretty
```
