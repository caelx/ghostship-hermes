---
name: pyload-ng
description: Use when you need pyLoad-ng REST operations exposed directly as exact method-name commands.
---

# ghostship-pyload-ng

- Commands mirror the API/client method names exactly. Do not guess aliases.
- Every invocation accepts `--timeout`; default hard timeout is `30` seconds.
- Where the service exposes write/delete operations, those commands support `--dry-run` and print the exact request object without calling the API.
- Configure the utility with:
- `PYLOAD_URL`
- `PYLOAD_USER (optional)`
- `PYLOAD_PASS (optional)`
- Prefer the dedicated snake_case command first. Use `request` only as fallback.

## Common Commands
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
