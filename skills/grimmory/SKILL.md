---
name: grimmory
description: Manage book library via Grimmory. Output is native JSON.
---

# Grimmory Skill

The `ghostship-grimmory` utility allows agents to manage a book library via the Grimmory API (formerly BookLore). It supports listing books, libraries, authors, shelves, and triggering scans.

## Prerequisites

The following environment variables must be configured:
- `GRIMMORY_URL`: The base URL of the Grimmory instance.
- `GRIMMORY_TOKEN`: Your Bearer authentication token.

## Usage

All commands output native JSON.

### Commands

#### `ghostship-grimmory info`
Get system version and status information.

#### `ghostship-grimmory list-books`
List books in the library.
- `--page`: Page number (default: 0).
- `--size`: Records per page (default: 20).
- `--library-id`: Optional filter by library.

#### `ghostship-grimmory get-book <id>`
Get detailed metadata for a specific book.

#### `ghostship-grimmory list-libraries`
List all configured libraries and their paths.

#### `ghostship-grimmory scan`
Trigger a background scan of all configured libraries.

#### `ghostship-grimmory list-authors`
List all authors in the system.

#### `ghostship-grimmory list-shelves`
List all user-created shelves.

#### `ghostship-grimmory list-tasks`
List background tasks (e.g., ongoing scans, metadata updates).

## Examples

```bash
# Search for books (JSON processing recommended)
ghostship-grimmory list-books --pretty

# Start a library scan
ghostship-grimmory scan
```

## Agent Guidance

- Grimmory is used for digital book collections (EPUB, PDF, etc.).
- Use `list-libraries` to understand the library structure before filtering `list-books`.
- Trigger a `scan` if the filesystem has changed.
- Use `list-tasks` to monitor the progress of a scan.
