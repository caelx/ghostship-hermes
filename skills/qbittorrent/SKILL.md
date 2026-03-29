---
name: qbittorrent
description: Manage qBittorrent transfers, application settings, and logs. Output is native JSON.
---

# qBittorrent Skill

The `ghostship-qbittorrent` utility allows agents to manage torrent transfers, add new magnet links or URLs, control torrent states (pause/resume/delete), and manage application settings and logs.

## Structure

- **Skill Document:** `skills/qbittorrent/SKILL.md` (this file)
- **Package Directory:** `packages/qbittorrent-cli/`
- **README:** `packages/qbittorrent-cli/README.md`

## Prerequisites

The following environment variables must be configured:
- `QBIT_URL`: The base URL of the qBittorrent WebUI (e.g., `http://localhost:8080`).
- `QBIT_USER`: The username for authentication.
- `QBIT_PASS`: The password for authentication.

## Usage

All commands output native JSON.

### Commands

#### `ghostship-qbittorrent info`
Get global transfer information, including overall download/upload speeds and DHT node count.

#### `ghostship-qbittorrent app-info`
Get application version and WebAPI version.

#### `ghostship-qbittorrent prefs`
Get all application preferences (settings).

#### `ghostship-qbittorrent log [--last-id <id>]`
Get the application main log.
- `--last-id`: ID of the last known log message to get only newer ones.

#### `ghostship-qbittorrent list-torrents`
List all torrents currently in the queue.
- `--filter`: Optional filter (e.g., `downloading`, `completed`, `paused`, `active`).
- `--category`: Optional category filter.

#### `ghostship-qbittorrent add <urls>`
Add one or more magnet links or torrent URLs.
- `urls`: One or more URLs (space-separated in CLI).

#### `ghostship-qbittorrent pause <hashes>`
Pause one or more torrents.
- `hashes`: One or more torrent hashes.

#### `ghostship-qbittorrent resume <hashes>`
Resume one or more torrents.
- `hashes`: One or more torrent hashes.

#### `ghostship-qbittorrent delete <hashes>`
Delete one or more torrents.
- `hashes`: One or more torrent hashes.
- `--delete-files`: Also delete the downloaded data from disk.

#### `ghostship-qbittorrent search <pattern>`
Start an asynchronous search for torrents.
- `pattern`: Search term.
- `--category`: Optional category (default: `all`).

#### `ghostship-qbittorrent search-results <search_id>`
Retrieve results from a search task.
- `search_id`: ID returned by the `search` command.

#### `ghostship-qbittorrent rss`
Get all RSS feeds and their items.

## Examples

```bash
# Check global speeds
ghostship-qbittorrent info

# List downloading torrents in a specific category
ghostship-qbittorrent list-torrents --filter downloading --category movies --pretty

# Start a search
ghostship-qbittorrent search "Big Buck Bunny"
# Use the task ID from above to get results
ghostship-qbittorrent search-results 123
```

## Agent Guidance

- Use `list-torrents` with filters to quickly find relevant torrents.
- Torrent hashes are the unique identifiers used for `pause`, `resume`, and `delete`.
- Always confirm with the user before using `--delete-files` as this action is irreversible.
- Use `prefs` to check or help the user configure their qBittorrent instance.
- RSS data can be used to monitor automated release feeds.
