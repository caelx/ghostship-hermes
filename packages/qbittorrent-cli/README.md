# ghostship-qbittorrent

`ghostship-qbittorrent` is a JSON-first CLI for its service API. Commands mirror the client/API method names exactly. No compatibility aliases are provided.

## Environment
- `QBITTORRENT_URL`
- `QBITTORRENT_USER (optional)`
- `QBITTORRENT_PASS (optional)`

## Command Contract
- Primary commands use the exact snake_case client method names.
- Use `request` only for endpoints that are not covered by a dedicated wrapper yet.
- Output is JSON by default.
- Every invocation accepts `--timeout`; the default hard timeout is `30` seconds.
- Where a service exposes write or delete operations, those commands accept `--dry-run` and print the exact request object instead of calling the API.

## Commands
- `ghostship-qbittorrent request`
- `ghostship-qbittorrent login`
- `ghostship-qbittorrent logout`
- `ghostship-qbittorrent get_app_version`
- `ghostship-qbittorrent get_api_version`
- `ghostship-qbittorrent shutdown`
- `ghostship-qbittorrent get_preferences`
- `ghostship-qbittorrent set_preferences`
- `ghostship-qbittorrent get_log`
- `ghostship-qbittorrent get_main_data`
- `ghostship-qbittorrent get_transfer_info`
- `ghostship-qbittorrent get_speed_limits_mode`
- `ghostship-qbittorrent toggle_speed_limits_mode`
- `ghostship-qbittorrent get_torrents`
- `ghostship-qbittorrent add_torrent`
- `ghostship-qbittorrent delete_torrents`
- `ghostship-qbittorrent pause_torrents`
- `ghostship-qbittorrent resume_torrents`
- `ghostship-qbittorrent search_start`
- `ghostship-qbittorrent search_status`
- `ghostship-qbittorrent search_results`
- `ghostship-qbittorrent get_rss_data`

## Examples
```bash
ghostship-qbittorrent get_transfer_info --pretty
```
```bash
ghostship-qbittorrent get_torrents --pretty
```
```bash
ghostship-qbittorrent search_start ubuntu
```
