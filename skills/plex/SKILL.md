---
name: plex
description: Manage Plex Media Server library, sessions, and settings. Output is native JSON.
---

# Plex Skill

The `ghostship-plex` utility allows agents to manage a Plex Media Server, including library management, metadata retrieval, session monitoring, maintenance tasks, and server preferences.

## Prerequisites

The following environment variables must be configured:
- `PLEX_URL`: The base URL of the Plex Media Server (e.g., `http://192.168.1.100:32400`).
- `PLEX_TOKEN`: Your Plex authentication token.

## Usage

All commands output native JSON.

### Commands

#### `ghostship-plex info`
Get server identity and status information, including version and machine identifier.

#### `ghostship-plex libraries`
List all library sections configured on the server.

#### `ghostship-plex library <section_id>`
List all items (metadata) within a specific library section.

#### `ghostship-plex refresh [--id <id>]`
Refresh one or all library sections to discover new media.

#### `ghostship-plex sessions`
View active media playback sessions, including user details, titles, and progress.

#### `ghostship-plex metadata <rating_key> [--children]`
Get detailed metadata for a specific media item.
- `--children`: List children of the item (e.g., episodes of a show, tracks of an album).

#### `ghostship-plex playlists`
List all playlists on the server.

#### `ghostship-plex collections <section_id>`
List all collections within a specific library section.

#### `ghostship-plex prefs`
Get all server preferences and settings.

#### `ghostship-plex tasks`
List scheduled maintenance (Butler) tasks and their status.

## Examples

```bash
# Search for a specific movie in library 1
ghostship-plex library 1 --pretty

# Check if anyone is watching a specific item
ghostship-plex sessions --pretty
```

## Agent Guidance

- Use `libraries` to find the `section_id` for other commands.
- `metadata --children` is essential for navigating TV show hierarchies (Show -> Season -> Episode).
- Preferences (`prefs`) can be used to check server configuration like remote access or transcoder settings.
- The `rating_key` is the unique identifier for items within Plex libraries.
