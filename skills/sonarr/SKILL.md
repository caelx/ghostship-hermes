---
name: sonarr
description: Manage TV series library via Sonarr. Output is native JSON.
---

# Sonarr Skill

The `ghostship-sonarr` utility allows agents to manage a TV series library, search for new content, and monitor download progress.

## Structure

- **Skill Document:** `skills/sonarr/SKILL.md` (this file)
- **Package Directory:** `packages/sonarr-cli/`
- **README:** `packages/sonarr-cli/README.md`

## Prerequisites

The following environment variables must be configured:
- `SONARR_URL`: The base URL of the Sonarr instance.
- `SONARR_API_KEY`: The API key for authentication.

## Usage

All commands output native JSON.

### Commands

#### `ghostship-sonarr info`
Get system status and version information.

#### `ghostship-sonarr list-series`
List all series currently in the library.

#### `ghostship-sonarr lookup "<term>"`
Search for a series by name to get its metadata and ID (TVDB).

#### `ghostship-sonarr get-series <id>`
Get detailed information for a specific series by its internal Sonarr ID.

#### `ghostship-sonarr add <tvdb_id> <title>`
Add a new series to the library.
- `tvdb_id`: The TVDB ID from `lookup`.
- `title`: The title of the series.
- `--quality-profile-id`: ID of the quality profile (default: 1).
- `--language-profile-id`: ID of the language profile (default: 1).
- `--root-folder-path`: Path where files will be stored (default: `/tv`).
- `--monitored`: Whether to monitor for new episodes (default: `True`).

#### `ghostship-sonarr history`
View the history of recent events (downloads, imports, etc.).
- `--page`: Page number (default: 1).
- `--page-size`: Records per page (default: 10).

#### `ghostship-sonarr queue`
View current download and import queue.

#### `ghostship-sonarr command <name>`
Trigger a long-running system command.
- `name`: Command name (e.g., `RescanSeries`, `EpisodeSearch`).
- `--args`: Optional JSON string of arguments for the command.

## Examples

```bash
# Search for a series
ghostship-sonarr lookup "Breaking Bad"

# Add a series (using TVDB ID from lookup)
ghostship-sonarr add 75710 "Breaking Bad"

# Check what's downloading
ghostship-sonarr queue --pretty
```

## Agent Guidance

- Use `lookup` before `add` to ensure the correct `tvdb_id` and title are used.
- Monitor `queue` to check if content is being downloaded.
- Use `history` to verify if content was successfully imported.
- When adding content, ensure the `root-folder-path` is consistent with the server's filesystem layout.
