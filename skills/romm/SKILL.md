---
name: romm
description: Use when you need RomM library, ROM, scan, save, and user operations through direct client method names.
---

# ghostship-romm

- Commands mirror the API/client method names exactly. Do not guess aliases.
- Configure the utility with:
- `ROMM_URL`
- `ROMM_TOKEN or ROMM_USERNAME and ROMM_PASSWORD`
- Prefer the dedicated snake_case command first. Use `request` only as fallback.

## Common Commands
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
