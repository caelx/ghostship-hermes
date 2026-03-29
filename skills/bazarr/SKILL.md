---
name: bazarr
description: Manage subtitles via Bazarr. Output is native JSON.
---

# Bazarr Skill

The `ghostship-bazarr` utility allows agents to manage subtitle requirements for movies and TV series via the Bazarr API.

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
