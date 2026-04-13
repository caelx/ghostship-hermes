## Why

Ghostship currently has no `ghostship-bookstack` utility, which blocks agent workflows that need to read and manage BookStack wiki content through the same JSON-first CLI surface used for the rest of the stack. BookStack is broad enough that a partial wrapper would create false confidence, so this change needs to define the utility and the shared transport behaviors required to support the full upstream API contract.

## What Changes

- Add a new `ghostship-bookstack` utility package that exposes the full BookStack REST API through repo-standard `ghostship-*` client and CLI patterns.
- Pull down the official BookStack API documentation at proposal and implementation time, commit the canonical repo reference under `docs/api/`, and use that captured contract to drive the utility surface.
- Add a repo-owned BookStack API reference sheet that records auth, endpoint groups, pagination/filtering rules, and the source quality of the captured docs artifact.
- Extend the shared CLI/client contract so full-surface utilities can represent multipart form uploads and non-JSON/binary response endpoints in a first-class way instead of falling back to JSON-only assumptions.
- Keep the repo-wide CLI contract intact: native JSON output by default, `--timeout` defaulting to 30 seconds, dry-run support for writes/deletes, and a generic escape-hatch request command for temporary upstream drift.

## Capabilities

### New Capabilities
- `bookstack-cli`: Full BookStack REST API coverage through a new `ghostship-bookstack` utility, including committed repo docs and per-operation CLI commands.
- `shared-cli-rich-http-surface`: Shared `ghostship-*` transport support for multipart form requests and binary/non-JSON endpoint handling needed by full-surface utilities such as BookStack.

### Modified Capabilities
- None.

## Impact

- Affected code: new `packages/bookstack-cli` package, `docs/api/bookstack.*` artifacts, shared CLI contract/helpers, packaging/Nix wiring, and utility test coverage.
- Affected APIs: BookStack REST API auth and endpoint coverage, especially attachment/image/import uploads and export/image-data downloads.
- Dependencies/systems: BookStack instance docs capture, Python utility packaging, and any shared request/response helpers used by other full-surface CLIs.
