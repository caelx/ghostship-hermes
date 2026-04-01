# ghostship-grimmory

`ghostship-grimmory` is a JSON-first CLI for its service API. Commands mirror the client/API method names exactly. No compatibility aliases are provided.

## Environment
- `GRIMMORY_URL`
- `GRIMMORY_TOKEN or GRIMMORY_USERNAME and GRIMMORY_PASSWORD`

## Command Contract
- Primary commands use the exact snake_case client method names.
- Use `request` only for endpoints that are not covered by a dedicated wrapper yet.
- Output is JSON by default.
- Every invocation accepts `--timeout`; the default hard timeout is `30` seconds.
- Where a service exposes write or delete operations, those commands accept `--dry-run` and print the exact request object instead of calling the API.

## Commands
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
