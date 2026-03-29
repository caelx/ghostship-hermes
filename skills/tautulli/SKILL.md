---
name: tautulli
description: Monitor Plex activity and history via Tautulli. Output is native JSON.
---

# Tautulli Skill

The `ghostship-tautulli` utility allows agents to monitor Plex Media Server activity, playback history, and user statistics via the Tautulli API. It provides a more analytical view of Plex usage than the native Plex API.

## Prerequisites

The following environment variables must be configured:
- `TAUTULLI_URL`: The base URL of the Tautulli instance.
- `TAUTULLI_API_KEY`: The API key for authentication.

## Usage

All commands output native JSON.

### Commands

#### `ghostship-tautulli info`
Get Tautulli server information and connection status to Plex.

#### `ghostship-tautulli activity`
Get current streaming activity, including progress, state, and user details.

#### `ghostship-tautulli history`
Get playback history.
- `--page`: Page number (default: 1).
- `--length`: Number of records per page (default: 10).
- `--search`: Search for specific titles or users in history.

#### `ghostship-tautulli users`
List all users tracked by Tautulli.

#### `ghostship-tautulli user-stats <user_id>`
Get detailed playback and watch time statistics for a specific user.

#### `ghostship-tautulli libraries`
List all library sections tracked by Tautulli.

#### `ghostship-tautulli search <query>`
Search for media items via Tautulli (querying the Plex database).

#### `ghostship-tautulli terminate <session_id> [--message <msg>]`
Terminate an active streaming session.
- `--message`: Optional message to display to the user on their Plex client.

## Examples

```bash
# Check what's being watched right now
ghostship-tautulli activity --pretty

# Find how much a user has watched
ghostship-tautulli user-stats 123 --pretty
```

## Agent Guidance

- Use `activity` for real-time monitoring.
- `user-stats` is excellent for understanding a user's preferences and most-watched content.
- Use `search` when you need to find where a specific item is located across all libraries.
- Tautulli's `user_id` corresponds to the Plex user ID.
