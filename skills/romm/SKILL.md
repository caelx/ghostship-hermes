---
name: romm
description: Manage ROM library via Romm. Output is native JSON.
---

# Romm Skill

The `ghostship-romm` utility allows agents to manage a ROM and game library via the Romm API (v4.7.0+). It supports library scanning, metadata retrieval, and platform management.

## Structure

- **Skill Document:** `skills/romm/SKILL.md` (this file)
- **Package Directory:** `packages/romm-cli/`
- **README:** `packages/romm-cli/README.md`

## Prerequisites

The following environment variables must be configured:
- `ROMM_URL`: The base URL of the Romm instance.
- `ROMM_TOKEN`: Your Bearer authentication token.

## Usage

All commands output native JSON.

### Commands

#### `ghostship-romm heartbeat`
Check the API heartbeat and basic configuration.

#### `ghostship-romm list-roms`
List ROMs in the library.
- `--page`: Page number (default: 1).
- `--page-size`: Records per page (default: 24).
- `--platform`: Optional platform slug to filter by.

#### `ghostship-romm get-rom <id>`
Get detailed information for a specific ROM by its ID.

#### `ghostship-romm platforms`
List all available platforms and their game counts.

#### `ghostship-romm list-collections`
List all user collections.

#### `ghostship-romm scan [--id <id>]`
Start a library scan.
- `--id`: Optional library ID to scan a specific library.

#### `ghostship-romm config`
Get the Romm system configuration.

#### `ghostship-romm saves [--page <n>] [--page-size <n>]`
List save files in the library.
- `--page`: Page number (default: 1).
- `--page-size`: Records per page (default: 24).

#### `ghostship-romm saves-summary`
Get a summary of all save files across all platforms.

#### `ghostship-romm users`
List all users on the Romm instance.

#### `ghostship-romm me`
Get current authenticated user information.

## Examples

```bash
# Check connectivity
ghostship-romm heartbeat

# List SNES games
ghostship-romm list-roms --platform snes --pretty

# Start a scan
ghostship-romm scan
```

## Agent Guidance

- Use `heartbeat` to verify the service is up and the token is valid.
- `list-roms` and `get-rom` provide extensive metadata including file paths and release years.
- When helping users find games, `platforms` can be used to see which consoles are supported.
