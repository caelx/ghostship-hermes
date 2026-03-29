---
name: nzbget
description: Manage NZBGet download queue and server. Output is native JSON.
---

# NZBGet Skill

The `ghostship-nzbget` utility allows agents to manage the NZBGet download queue, add new NZB URLs, and control the server state (pause/resume/rate/shutdown).

## Prerequisites

The following environment variables must be configured:
- `NZBGET_URL`: The base URL of the NZBGet instance (e.g., `http://localhost:6789`).
- `NZBGET_USER`: The username for authentication.
- `NZBGET_PASS`: The password for authentication.

## Usage

All commands output native JSON.

### Commands

#### `ghostship-nzbget info`
Get global status information, including download speed, remaining size, and server state.

#### `ghostship-nzbget version`
Get NZBGet version.

#### `ghostship-nzbget list-queue`
List all downloads currently in the queue.

#### `ghostship-nzbget list-files <nzb_id>`
List files in a specific NZB group.

#### `ghostship-nzbget history`
Get download history.

#### `ghostship-nzbget add <url>`
Add an NZB URL to the download queue.
- `url`: The URL of the NZB file.
- `--category`: Optional category for the download.
- `--priority`: Optional priority (default: 0).

#### `ghostship-nzbget pause`
Pause the NZBGet download queue.

#### `ghostship-nzbget resume`
Resume the NZBGet download queue.

#### `ghostship-nzbget rate <limit_kb>`
Set download speed limit in KB/s (0 for unlimited).

#### `ghostship-nzbget config`
Get the NZBGet system configuration.

#### `ghostship-nzbget shutdown`
Shutdown the NZBGet server.

## Examples

```bash
# Check status and speed
ghostship-nzbget info --pretty

# Add a new download
ghostship-nzbget add "https://example.com/file.nzb" --category movies

# Set speed limit to 5MB/s
ghostship-nzbget rate 5120
```

## Agent Guidance

- Use `info` to check if the server is paused before reporting download issues to the user.
- The `nzbid` returned by `add` can be used to track the specific download or list its files using `list-files`.
- Be cautious with the `shutdown` command as it will stop the service entirely.
