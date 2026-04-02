---
name: pyload-ng
description: Operate pyLoad-ng from the Hermes image with `ghostship-pyload-ng`. Use when checking server status, queue, downloads, accounts, config, free space, or when adding packages and files, deleting finished work, managing accounts, or toggling pause state through exact snake_case CLI operations.
---

# pyLoad-ng Skill

Use `ghostship-pyload-ng` for download workflows that begin with queue and server inspection before mutating packages or accounts.

## Prerequisites

- `PYLOAD_URL`
- `PYLOAD_USER` and `PYLOAD_PASS` when auth is required

## Operating Model

- Prefer dedicated snake_case commands first.
- Use `request` only for uncovered endpoints.
- Every command accepts `--timeout`; default hard timeout is `30` seconds.
- Write and delete operations support `--dry-run`.

## Start Here

- Server health: `ghostship-pyload-ng get_server_status`, `ghostship-pyload-ng get_server_version`, `ghostship-pyload-ng get_free_space`
- Queue and downloads: `ghostship-pyload-ng get_queue`, `ghostship-pyload-ng get_downloads`
- Account state: `ghostship-pyload-ng get_accounts`
- Troubleshooting: `ghostship-pyload-ng get_config`

## Common Workflows

- Diagnose a stuck downloader:
  - `get_server_status`
  - `get_queue`
  - `get_downloads`
  - `get_accounts`
- Add download work:
  - `add_package --dry-run ...` or `add_files --dry-run ...`
  - execute once the request shape is correct
  - `get_queue` to verify acceptance
- Clean up or retry:
  - Inspect current queue or completed state first.
  - `delete_finished --dry-run ...` or `restart_failed --dry-run ...`
  - Re-read queue or downloads afterward.
- Manage accounts:
  - `get_accounts`
  - `add_account --dry-run ...` or `remove_account --dry-run ...`
  - Re-read account state to verify.

## Mutation Guardrails

- Confirm package or account targets before mutating.
- Use `--dry-run` for adds, deletions, retries, and account changes.
- Treat `stop_all_downloads` and `toggle_pause` as explicit operator actions after reading current server status.

## Fallback

- Use `ghostship-pyload-ng request` only for uncovered endpoints.
