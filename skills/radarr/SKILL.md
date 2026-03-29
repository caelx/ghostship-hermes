---
name: radarr
description: Manage movie library via Radarr. Output is native JSON.
---

# Radarr Skill

The `ghostship-radarr` utility allows agents to manage a movie library, search for new content, and monitor download progress.

## Structure

- **Skill Document:** `skills/radarr/SKILL.md` (this file)
- **Package Directory:** `packages/radarr-cli/`
- **README:** `packages/radarr-cli/README.md`

## Prerequisites

The following environment variables must be configured:
- `RADARR_URL`: The base URL of the Radarr instance.
- `RADARR_API_KEY`: The API key for authentication.

## Usage

All commands output native JSON.

### Commands

#### `ghostship-radarr info`
Get system status and version information.

#### `ghostship-radarr list-movies`
List all movies currently in the library.

#### `ghostship-radarr lookup "<term>"`
Search for a movie by name to get its metadata and ID (TMDB).

#### `ghostship-radarr get-movie <id>`
Get detailed information for a specific movie by its internal Radarr ID.

#### `ghostship-radarr add <tmdb_id> <title>`
Add a new movie to the library.
- `tmdb_id`: The TMDB ID from `lookup`.
- `title`: The title of the movie.
- `--quality-profile-id`: ID of the quality profile (default: 1).
- `--root-folder-path`: Path where files will be stored (default: `/movies`).
- `--monitored`: Whether to monitor for the movie (default: `True`).

#### `ghostship-radarr history`
View the history of recent events (downloads, imports, etc.).
- `--page`: Page number (default: 1).
- `--page-size`: Records per page (default: 10).

#### `ghostship-radarr queue`
View current download and import queue.

#### `ghostship-radarr command <name>`
Trigger a long-running system command.
- `name`: Command name (e.g., `MoviesSearch`, `RescanMovie`).
- `--args`: Optional JSON string of arguments for the command.

## Examples

```bash
# Search for a movie
ghostship-radarr lookup "Inception"

# Add a movie (using TMDB ID from lookup)
ghostship-radarr add 27205 "Inception"

# List movies in library
ghostship-radarr list-movies --pretty
```

## Agent Guidance

- Use `lookup` before `add` to ensure the correct `tmdb_id` and title are used.
- Monitor `queue` to check if content is being downloaded.
- Use `history` to verify if content was successfully imported.
- When adding content, ensure the `root-folder-path` is consistent with the server's filesystem layout.
