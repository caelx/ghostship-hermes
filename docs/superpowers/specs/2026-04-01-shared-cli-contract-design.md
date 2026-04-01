# Shared CLI Contract Design

## Summary
This design standardizes every `ghostship-*` utility around a shared transport and CLI contract. The goal is to make all utilities behave the same way for timeouts, dry runs, exit codes, and JSON errors while keeping service-specific command names aligned with API/client operation names.

## Goals
- Standardize a default hard timeout of `30.0` seconds for all network operations.
- Add `--timeout` support to every CLI command that can reach a remote service.
- Add `--dry-run` support for every write/delete operation so the CLI prints the exact request object it would send without making a network call.
- Make JSON error output and process exit codes consistent across all utilities.
- Preserve the existing command-name rule: dedicated commands mirror API/client operation names exactly in snake_case, with no compatibility aliases.

## Non-Goals
- This refactor does not attempt to expand each service to a larger API surface than is already supported in the repo.
- This refactor does not make live integration tests perform writes for existing services; existing live coverage remains read-only.
- This refactor does not change service authentication models beyond normalizing how env vars are loaded and validated.

## Shared Package
Add a new shared Python package, tentatively `ghostship-cli-contract`, under `packages/ghostship-cli-contract/`.

Responsibilities:
- Provide a shared `RequestSpec` model that represents the exact outbound request shape.
- Provide a shared `ServiceError` hierarchy with fixed exit-code mapping.
- Provide shared Typer-facing helpers for:
  - JSON output
  - JSON/body parsing
  - `key=value` param parsing
  - dry-run rendering
  - standardized command execution wrappers
- Provide a shared `BaseHttpClient` / transport helper for:
  - default timeout `30.0`
  - per-command timeout override
  - consistent no-content handling
  - consistent `httpx` exception translation
  - optional test-only Cloudflare Access headers

## Request Model
Every write/delete operation must be expressible as a `RequestSpec` before it executes.

Minimum fields:
- `method`
- `path`
- `params`
- `json_body`
- `form_data`
- `files`
- `headers`
- `timeout`

Dry-run output must be native JSON and include only the fields relevant to the outbound request. This JSON becomes the stable contract agents can inspect before execution.

## Error Contract
All CLI errors must print a JSON envelope to stderr:
- `error.type`
- `error.message`
- `error.details` when available
- `error.exit_code`

Fixed exit codes:
- `2`: invalid CLI input / validation failure
- `3`: missing required environment or auth configuration
- `4`: request timeout
- `5`: remote HTTP error response
- `6`: transport or connection failure
- `7`: response decoding / unexpected response format
- `10`: unknown internal CLI failure

## Client Structure
Each service client should converge on this structure:
- read methods may call transport directly
- write/delete methods must have a request-builder form that returns `RequestSpec`
- execute methods use the built spec and return parsed service JSON

Preferred pattern:
- `build_<operation>_request(...) -> RequestSpec`
- `<operation>(..., timeout: float | None = None) -> Any`

This keeps dry-run behavior stable and avoids duplicating payload-building logic in the CLI layer.

## CLI Structure
Every CLI command should accept:
- `--pretty` for output formatting where already supported
- `--timeout FLOAT` for any command that could do I/O, defaulting to the shared 30-second timeout

Every write/delete command should also accept:
- `--dry-run`

Behavior:
- with `--dry-run`, print the built `RequestSpec` JSON and exit `0`
- without `--dry-run`, execute normally and print service JSON

## Migration Scope
Migrate every current utility in this repo to the shared package:
- bazarr
- cloakbrowser
- flaresolverr
- grimmory
- nzbget
- plex
- pricebuddy
- prowlarr
- pyload-ng
- qbittorrent
- radarr
- romm
- rss-bridge
- searxng
- sonarr
- synology
- tautulli

## Testing
Unit tests must cover:
- shared package request/error/timeout helpers
- request builders for all write/delete commands
- CLI dry-run output
- timeout plumb-through
- stable exit code mapping

Live integration tests remain read-only for existing services. They should verify the new timeout flag on representative reads but should not be expanded to write coverage except where already approved separately.

## Documentation
Update:
- top-level `README.md`
- `CHANGELOG.md`
- `AGENTS.md`
- package READMEs for every migrated utility
- relevant skills so Hermes knows every CLI supports `--timeout` and write/delete `--dry-run`

## Risks
- Some clients currently use different request shapes (`json`, form data, XML/JSON-RPC, query-only actions). `RequestSpec` must support all of them without forcing a false REST model.
- Some packages currently use small handwritten wrappers rather than structured builder methods. Migration must preserve command names and response behavior while normalizing the transport contract.
- Existing tests assume old failure modes. They must be updated to the new error envelope and exit codes.
