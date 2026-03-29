---
name: pyload-ng
description: Manage downloads and packages via the pyLoad-ng API. Output is native JSON.
---

# pyLoad-ng Skill

The `ghostship-pyload-ng` utility allows agents to manage downloads, packages, and server status via the pyLoad-ng REST API.

## Structure

- **Skill Document:** `skills/pyload-ng/SKILL.md` (this file)
- **Package Directory:** `packages/pyload-ng-cli/`
- **README:** `packages/pyload-ng-cli/README.md`

## Prerequisites

The following environment variables must be configured:
- `PYLOAD_URL`: The base URL of the pyLoad-ng instance (e.g., `http://localhost:8000`).
- `PYLOAD_USER`: Your pyLoad-ng username.
- `PYLOAD_PASS`: Your pyLoad-ng password.

## Usage

All commands output native JSON.

### Commands

#### `ghostship-pyload-ng status`
Get general information about the current status of pyLoad.

#### `ghostship-pyload-ng downloads`
Get status of all currently running downloads.

#### `ghostship-pyload-ng queue`
List all packages in the queue.

#### `ghostship-pyload-ng add <name> <links...>`
Add a new package with the specified name and list of URLs.

#### `ghostship-pyload-ng add-to-package <package_id> <links...>`
Add one or more links to an existing package.

#### `ghostship-pyload-ng delete <package_ids...>`
Delete one or more packages by their IDs.

#### `ghostship-pyload-ng pause`
Toggle the pause/resume state of the server.

## Examples

```bash
# Check server status
ghostship-pyload-ng status --pretty

# Add a new download package
ghostship-pyload-ng add "My Files" "http://example.com/file1.zip" "http://example.com/file2.zip"

# List current downloads
ghostship-pyload-ng downloads --pretty
```

## Agent Guidance

- Use `ghostship-pyload-ng status` to check if the server is paused or to see global download speeds.
- Use `ghostship-pyload-ng queue` to find `package_id`s for management tasks.
- For many links, prefer creating a package via `add` rather than adding to existing ones individually.
