---
name: nzbget
description: Use when you need NZBGet JSON-RPC methods exposed directly as snake_case commands.
---

# ghostship-nzbget

- Commands mirror the API/client method names exactly. Do not guess aliases.
- Configure the utility with:
- `NZBGET_URL`
- `NZBGET_USER`
- `NZBGET_PASS`
- Prefer the dedicated snake_case command first. Use `call` only as fallback.

## Common Commands
- `ghostship-nzbget call`
- `ghostship-nzbget get_version`
- `ghostship-nzbget shutdown`
- `ghostship-nzbget reload`
- `ghostship-nzbget get_status`
- `ghostship-nzbget list_groups`
- `ghostship-nzbget list_files`
- `ghostship-nzbget get_history`
- `ghostship-nzbget append_url`
- `ghostship-nzbget edit_queue`
- `ghostship-nzbget disk_scan`
- `ghostship-nzbget get_log`
- `ghostship-nzbget set_rate`
- `ghostship-nzbget pause_download`
- `ghostship-nzbget resume_download`
- `ghostship-nzbget pause_post`
- `ghostship-nzbget resume_post`
- `ghostship-nzbget pause_scan`
- `ghostship-nzbget resume_scan`
- `ghostship-nzbget get_config`
- `ghostship-nzbget save_config`

## Examples
```bash
ghostship-nzbget get_status --pretty
```
```bash
ghostship-nzbget list_groups --pretty
```
```bash
ghostship-nzbget call version
```
