---
name: bazarr
description: Manage subtitles via Bazarr. Output is native JSON.
---

# Bazarr Skill

The `ghostship-bazarr` utility allows agents to manage subtitle requirements for movies and TV series via the Bazarr API.

## Structure

- **Skill Document:** `skills/bazarr/SKILL.md` (this file)
- **Package Directory:** `packages/bazarr-cli/`
- **README:** `packages/bazarr-cli/README.md`

## Prerequisites

The following environment variables must be configured:
- `BAZARR_URL`: The base URL of the Bazarr instance.
- `BAZARR_API_KEY`: The API key for authentication.

## Usage

All commands output native JSON.

### Commands

#### `ghostship-bazarr info`
Get system status information, including version and Python environment.

#### `ghostship-bazarr list-series`
List all TV series in the library and their monitoring status for subtitles.

#### `ghostship-bazarr history [--media episodes|movies]`
Get subtitle download history.
- `--media`: Filter by `episodes` (default) or `movies`.

#### `ghostship-bazarr blacklist [--media episodes|movies]`
Get blocklisted subtitles (downloads that failed or were rejected).
- `--media`: Filter by `episodes` (default) or `movies`.

## Examples

```bash
# Check system status
ghostship-bazarr info

# List series to check subtitle status
ghostship-bazarr list-series --pretty
```

## Agent Guidance

- Use `list-series` to identify which shows are currently being managed by Bazarr.
- Agents can use this tool to verify if subtitles are missing or being searched for when users report issues with media playback.
