---
name: prowlarr
description: Use when you need Prowlarr indexer, app, history, and command endpoints with direct method-name commands.
---

# ghostship-prowlarr

- Commands mirror the API/client method names exactly. Do not guess aliases.
- Every invocation accepts `--timeout`; default hard timeout is `30` seconds.
- Where the service exposes write/delete operations, those commands support `--dry-run` and print the exact request object without calling the API.
- Configure the utility with:
- `PROWLARR_URL`
- `PROWLARR_API_KEY`
- Prefer the dedicated snake_case command first. Use `request` only as fallback.

## Common Commands
- `ghostship-prowlarr request`
- `ghostship-prowlarr get_status`
- `ghostship-prowlarr get_indexers`
- `ghostship-prowlarr search`
- `ghostship-prowlarr get_applications`
- `ghostship-prowlarr get_history`
- `ghostship-prowlarr get_indexer_stats`
- `ghostship-prowlarr get_indexer_status`
- `ghostship-prowlarr run_command`

## Examples
```bash
ghostship-prowlarr get_indexers --pretty
```
```bash
ghostship-prowlarr search ubuntu --pretty
```
```bash
ghostship-prowlarr run_command ApplicationIndexerSync
```
