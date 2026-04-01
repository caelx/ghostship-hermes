# ghostship-pyload-ng

`ghostship-pyload-ng` is a JSON-first CLI for its service API. Commands mirror the client/API method names exactly. No compatibility aliases are provided.

## Environment
- `PYLOAD_URL`
- `PYLOAD_USER (optional)`
- `PYLOAD_PASS (optional)`

## Command Contract
- Primary commands use the exact snake_case client method names.
- Use `request` only for endpoints that are not covered by a dedicated wrapper yet.
- Output is JSON by default.

## Commands
- `ghostship-pyload-ng request`
- `ghostship-pyload-ng get_server_status`
- `ghostship-pyload-ng get_downloads`
- `ghostship-pyload-ng get_queue`
- `ghostship-pyload-ng add_package`
- `ghostship-pyload-ng add_files`
- `ghostship-pyload-ng delete_packages`
- `ghostship-pyload-ng toggle_pause`
- `ghostship-pyload-ng get_config`
- `ghostship-pyload-ng delete_finished`
- `ghostship-pyload-ng restart_failed`
- `ghostship-pyload-ng stop_all_downloads`
- `ghostship-pyload-ng get_accounts`
- `ghostship-pyload-ng add_account`
- `ghostship-pyload-ng remove_account`
- `ghostship-pyload-ng get_server_version`
- `ghostship-pyload-ng get_free_space`

## Examples
```bash
ghostship-pyload-ng get_server_status --pretty
```
```bash
ghostship-pyload-ng get_queue --pretty
```
```bash
ghostship-pyload-ng get_accounts --refresh
```
