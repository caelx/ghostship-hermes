# chaptarr-cli Specification

## Purpose

Provide a repo-owned `ghostship-chaptarr` wrapper that makes the Chaptarr Readarr-derived public API fully available via the shared Ghostship CLI contract and keeps the official OpenAPI materialized inside the repo.

## Requirements

### Requirement: The Hermes image SHALL bundle `ghostship-chaptarr` and expose it on `PATH`
- WHEN the image is built, the `ghostship-chaptarr` package must be present alongside the other repo utilities.
- THEN `ghostship-chaptarr` is available in the managed Hermes runtime without an extra installation step.

### Requirement: `ghostship-chaptarr` SHALL cover every upstream OpenAPI operation with a dedicated snake_case command
- WHEN maintainers compare the mirrored spec (`docs/api/chaptarr-openapi.json`) to the CLI catalog, every path/method pair should have its own typed command or clearly documented alias.
- THEN there is still a generic `request` command for uncommon or new endpoints, but the official contract is fully covered.

### Requirement: The CLI SHALL follow the shared Ghostship CLI contract
- WHEN users run `ghostship-chaptarr --help` and the subcommand help, every command accepts `--timeout` (default 30 seconds) and writes JSON by default.
- WHEN executing write/delete operations, the commands accept `--dry-run` and print the request object instead of hitting the API.

### Requirement: `ghostship-chaptarr` SHALL use environment-driven auth and path configuration
- WHEN the CLI boots, it reads `CHAPTARR_URL`, `CHAPTARR_API_KEY`, optional `CHAPTARR_API_PATH`, and optional `CHAPTARR_API_VERSION`.
- THEN requests are directed at `${CHAPTARR_URL}${CHAPTARR_API_PATH:-/api}/${CHAPTARR_API_VERSION:-v1}` with `X-Api-Key` set to `CHAPTARR_API_KEY`.

### Requirement: The repo SHALL document the official OpenAPI spec and environment contract
- WHEN the change is archived, `docs/api/chaptarr.md` explains auth, pagination, and endpoint groups, and `docs/api/README.md` lists the new entry and raw spec path.
- WHEN operators need to script against the module, the README/AGENTS sections highlight the required env variables and how to derive the API key from a running container.
