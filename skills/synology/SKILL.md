---
name: synology
description: Manage files on Synology NAS via File Station. Output is native JSON.
---

# Synology Skill

The `ghostship-synology` utility allows agents to manage files and folders on a Synology NAS using the File Station API. It supports listing shares, managing files (upload/download/rename/delete), and searching.

## Prerequisites

The following environment variables must be configured:
- `SYNOLOGY_URL`: The base URL of the Synology NAS (e.g., `https://192.168.1.10:5001`).
- `SYNOLOGY_USER`: Your DSM username.
- `SYNOLOGY_PASS`: Your DSM password.
- `SYNOLOGY_VERIFY_SSL`: Set to `false` if using self-signed certificates (default: `true`).

## Usage

All commands output native JSON.

### Commands

#### `ghostship-synology list-shares`
List all shared folders available on the NAS.

#### `ghostship-synology list-files <path>`
List files and subfolders in a specific path.
- `path`: The folder path (e.g., `/video`).
- `--offset`: Starting index (default: 0).
- `--limit`: Max items to return (default: 100).

#### `ghostship-synology info <path>`
Get detailed information (size, owner, timestamps) for a file or folder.

#### `ghostship-synology download <path>`
Download a file from the NAS to the local system.
- `path`: The file path on the NAS.
- `--output`: Local destination path (default: current directory).

#### `ghostship-synology search <folder_path> <pattern>`
Start an asynchronous search for files.
- `folder_path`: The folder to search within.
- `pattern`: The search pattern (e.g., `*.mkv`).
- `--no-recursive`: Disable recursive search (default: recursive).

#### `ghostship-synology search-results <taskid>`
Retrieve results from a search task started with `search`.

#### `ghostship-synology mkdir <path> <name>`
Create a new folder.
- `path`: The parent folder path.
- `name`: The name of the new folder.
- `--parents`: Create parent folders if they don't exist.

#### `ghostship-synology rename <path> <name>`
Rename a file or folder.
- `path`: Current path of the item.
- `name`: New name for the item.

#### `ghostship-synology rm <path>`
Delete a file or folder.
- `--no-recursive`: Disable recursive delete for folders.

## Examples

```bash
# List all shared folders
ghostship-synology list-shares --pretty

# Search for a file
ghostship-synology search "/video" "matrix"
# Use the taskid from above to get results
ghostship-synology search-results "task_123"

# Download a file
ghostship-synology download "/video/movie.mp4" --output "/home/hermes/downloads/"
```

## Agent Guidance

- Use `list-shares` first to understand the top-level directory structure.
- Searching is asynchronous; always check `search-results` after starting a `search`.
- When downloading, ensure the agent has write permissions to the destination directory.
- The utility handles login and logout automatically for each command.
