# ghostship-prowlarr

`ghostship-prowlarr` is a JSON-first CLI for its service API. Commands mirror the client/API method names exactly. No compatibility aliases are provided.

## Environment
- `PROWLARR_URL`
- `PROWLARR_API_KEY`

## Command Contract
- Primary commands use the exact snake_case client method names.
- Use `request` only for endpoints that are not covered by a dedicated wrapper yet.
- Output is JSON by default.
- Every invocation accepts `--timeout`; the default hard timeout is `30` seconds.
- Where a service exposes write or delete operations, those commands accept `--dry-run` and print the exact request object instead of calling the API.

## Commands
- `ghostship-prowlarr request`
- `ghostship-prowlarr get_status`
- `ghostship-prowlarr get_indexers`
- `ghostship-prowlarr search`
- `ghostship-prowlarr get_applications`
- `ghostship-prowlarr get_history`
- `ghostship-prowlarr get_indexer_stats`
- `ghostship-prowlarr get_indexer_status`
- `ghostship-prowlarr run_command`

## Examples
```bash
ghostship-prowlarr get_indexers --pretty
```
```bash
ghostship-prowlarr search ubuntu --pretty
```
```bash
ghostship-prowlarr run_command ApplicationIndexerSync
```
