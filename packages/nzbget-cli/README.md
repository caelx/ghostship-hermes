# ghostship-nzbget

`ghostship-nzbget` is a JSON-first CLI for its service API. Commands mirror the client/API method names exactly. No compatibility aliases are provided.

## Environment
- `NZBGET_URL`
- `NZBGET_USER`
- `NZBGET_PASS`

## Command Contract
- Primary commands use the exact snake_case client method names.
- Use `call` only for endpoints that are not covered by a dedicated wrapper yet.
- Output is JSON by default.

## Commands
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
