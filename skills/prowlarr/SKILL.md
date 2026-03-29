---
name: prowlarr
description: Manage indexers and search releases via Prowlarr. Output is native JSON.
---

# Prowlarr Skill

The `ghostship-prowlarr` utility allows agents to manage indexer configurations, search for releases (torrents/usenet) across all configured indexers, and manage connections to other applications.

## Structure

- **Skill Document:** `skills/prowlarr/SKILL.md` (this file)
- **Package Directory:** `packages/prowlarr-cli/`
- **README:** `packages/prowlarr-cli/README.md`

## Prerequisites

The following environment variables must be configured:
- `PROWLARR_URL`: The base URL of the Prowlarr instance.
- `PROWLARR_API_KEY`: The API key for authentication.

## Usage

All commands output native JSON.

### Commands

#### `ghostship-prowlarr info`
Get system status and version information.

#### `ghostship-prowlarr list-indexers`
List all configured indexers and their status.

#### `ghostship-prowlarr search "<query>"`
Search for releases across all indexers. This is useful for manual release discovery.

#### `ghostship-prowlarr list-apps`
List all connected applications (e.g., Sonarr, Radarr, Lidarr).

#### `ghostship-prowlarr indexer-stats`
Get statistics for all indexers, including number of queries, successful grabs, and failed grabs.

#### `ghostship-prowlarr indexer-status`
Get the current status of all indexers (enabled/disabled state).

## Examples

```bash
# List all indexers
ghostship-prowlarr list-indexers

# Search for a specific release
ghostship-prowlarr search "The Matrix 1999 2160p" --pretty

# Check connected apps
ghostship-prowlarr list_apps
```

## Agent Guidance

- Use `search` to check availability of specific releases when automated searches in Sonarr/Radarr are failing.
- Check `list-indexers` to ensure at least one indexer is enabled and healthy if search results are empty.
- Use `list-apps` to verify that Prowlarr is correctly synced with downstream applications.
