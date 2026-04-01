---
name: synology
description: Use when you need Synology File Station operations exposed directly as method-name commands.
---

# ghostship-synology

- Commands mirror the API/client method names exactly. Do not guess aliases.
- Every invocation accepts `--timeout`; default hard timeout is `30` seconds.
- Where the service exposes write/delete operations, those commands support `--dry-run` and print the exact request object without calling the API.
- Configure the utility with:
- `SYNOLOGY_URL`
- `SYNOLOGY_USER`
- `SYNOLOGY_PASS`
- `SYNOLOGY_VERIFY_SSL (optional)`
- Prefer the dedicated snake_case command first. Use `call` only as fallback.

## Common Commands
- `ghostship-synology call`
- `ghostship-synology get_info`
- `ghostship-synology login`
- `ghostship-synology logout`
- `ghostship-synology list_shares`
- `ghostship-synology list_files`
- `ghostship-synology get_file_info`
- `ghostship-synology search_start`
- `ghostship-synology search_list`
- `ghostship-synology create_folder`
- `ghostship-synology rename`
- `ghostship-synology delete`
- `ghostship-synology download_file`
- `ghostship-synology upload_file`
- `ghostship-synology copy`
- `ghostship-synology move`

## Examples
```bash
ghostship-synology list_shares --pretty
```
```bash
ghostship-synology list_files /video --limit 10 --pretty
```
```bash
ghostship-synology get_file_info /video/movie.mkv
```
