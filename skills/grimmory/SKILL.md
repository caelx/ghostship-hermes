---
name: grimmory
description: Use when you need Grimmory or BookLore reads and maintenance operations through direct client method names.
---

# ghostship-grimmory

- Commands mirror the API/client method names exactly. Do not guess aliases.
- Every invocation accepts `--timeout`; default hard timeout is `30` seconds.
- Where the service exposes write/delete operations, those commands support `--dry-run` and print the exact request object without calling the API.
- Configure the utility with:
- `GRIMMORY_URL`
- `GRIMMORY_TOKEN or GRIMMORY_USERNAME and GRIMMORY_PASSWORD`
- Prefer the dedicated snake_case command first. Use `request` only as fallback.

## Common Commands
- `ghostship-grimmory request`
- `ghostship-grimmory get_books`
- `ghostship-grimmory get_book`
- `ghostship-grimmory download_book`
- `ghostship-grimmory get_libraries`
- `ghostship-grimmory get_library`
- `ghostship-grimmory scan_libraries`
- `ghostship-grimmory refresh_library`
- `ghostship-grimmory get_authors`
- `ghostship-grimmory get_author`
- `ghostship-grimmory get_shelves`
- `ghostship-grimmory get_shelf_books`
- `ghostship-grimmory get_tasks`
- `ghostship-grimmory cancel_task`
- `ghostship-grimmory get_version`

## Examples
```bash
ghostship-grimmory get_books --page 0 --size 20 --pretty
```
```bash
ghostship-grimmory get_library 1
```
```bash
ghostship-grimmory scan_libraries
```
