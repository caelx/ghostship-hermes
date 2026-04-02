---
name: qbittorrent
description: Operate qBittorrent from the Hermes image with `ghostship-qbittorrent`. Use when checking transfer health, torrent state, logs, search jobs, RSS data, or when adding, pausing, resuming, deleting, or reconfiguring torrents through exact snake_case CLI operations.
---

# qBittorrent Skill

Use `ghostship-qbittorrent` for download workflows that start with transfer and torrent inspection before any queue mutation.

## Prerequisites

- `QBITTORRENT_URL`
- `QBITTORRENT_USER` and `QBITTORRENT_PASS` when auth is required

## Operating Model

- Prefer dedicated snake_case commands first.
- Use `request` only for uncovered endpoints.
- Every command accepts `--timeout`; default hard timeout is `30` seconds.
- Write and delete operations support `--dry-run`.

## Start Here

- Transfer health: `ghostship-qbittorrent get_transfer_info`, `ghostship-qbittorrent get_main_data`
- Torrent inventory: `ghostship-qbittorrent get_torrents`
- Server behavior: `ghostship-qbittorrent get_preferences`, `ghostship-qbittorrent get_log`
- Search or RSS workflows: `ghostship-qbittorrent search_status`, `ghostship-qbittorrent get_rss_data`

## Common Workflows

- Diagnose stalled downloads:
  - `get_transfer_info`
  - `get_torrents`
  - `get_log`
  - `get_speed_limits_mode`
- Add a torrent:
  - Inspect current queue or category expectations first.
  - `add_torrent --dry-run ...`, then `add_torrent ...`
  - `get_torrents` or `get_main_data` to verify acceptance.
- Pause, resume, or delete torrents:
  - Inspect target hashes with `get_torrents`.
  - `pause_torrents --dry-run ...`, `resume_torrents --dry-run ...`, or `delete_torrents --dry-run ...`
  - Re-read `get_torrents` afterward.
- Run a search flow:
  - `search_start "<query>"`
  - `search_status`
  - `search_results <id>`

## Mutation Guardrails

- Confirm torrent hashes before pause, resume, or delete operations.
- Use `--dry-run` for queue mutations and preference changes.
- Re-read torrent or transfer state after each action.

## Fallback

- Use `ghostship-qbittorrent request` only for uncovered endpoints.
