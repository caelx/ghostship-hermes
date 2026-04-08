# ghostship-chaptarr

`ghostship-chaptarr` is a JSON-first CLI that mirrors every endpoint in the official Chaptarr (Readarr fork) public API.

## Environment
- `CHAPTARR_URL` (required)
- `CHAPTARR_API_KEY` (required)
- `CHAPTARR_API_PATH` (optional, defaults to `/api`)
- `CHAPTARR_API_VERSION` (optional, defaults to `v1`)

`ghostship-chaptarr` automatically injects `X-Api-Key: <CHAPTARR_API_KEY>` on every request and builds URLs with the configured API path/version so self-hosted forks with alternate prefixes work out of the box.

## API Docs
Canonical API docs live under `docs/api/chaptarr.md`, and the mirrored OpenAPI spec is at `docs/api/chaptarr-openapi.json`.

## Command Contract
- Commands map one-to-one to the OpenAPI operations (snake_case names are derived from method + path).
- All commands accept `--timeout` (default 30 seconds), `--pretty`, and parameter options like `--path-param`/`--query-param`.
- Mutation commands also accept `--dry-run` so you can inspect the exact request JSON before calling the API.
