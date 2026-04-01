# ghostship-synology

`ghostship-synology` is a JSON-first CLI for its service API. Commands mirror the client/API method names exactly. No compatibility aliases are provided.

## Environment
- `SYNOLOGY_URL`
- `SYNOLOGY_USER`
- `SYNOLOGY_PASS`
- `SYNOLOGY_VERIFY_SSL (optional)`

## Command Contract
- Primary commands use the exact snake_case client method names.
- Use `call` only for endpoints that are not covered by a dedicated wrapper yet.
- Output is JSON by default.
- Every invocation accepts `--timeout`; the default hard timeout is `30` seconds.
- Where a service exposes write or delete operations, those commands accept `--dry-run` and print the exact request object instead of calling the API.

## Commands
- `ghostship-synology call`
- `ghostship-synology get_info`
- `ghostship-synology login`
- `ghostship-synology logout`
- `ghostship-synology list_shares`
- `ghostship-synology list_files`
- `ghostship-synology get_file_info`
- `ghostship-synology search_start`
- `ghostship-synology search_list`
- `ghostship-synology create_folder`
- `ghostship-synology rename`
- `ghostship-synology delete`
- `ghostship-synology download_file`
- `ghostship-synology upload_file`
- `ghostship-synology copy`
- `ghostship-synology move`

## Examples
```bash
ghostship-synology list_shares --pretty
```
```bash
ghostship-synology list_files /video --limit 10 --pretty
```
```bash
ghostship-synology get_file_info /video/movie.mkv
```
