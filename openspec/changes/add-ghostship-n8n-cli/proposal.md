## Why

Operators need a first-class `ghostship-*` utility for n8n that can manage the service through the supported public API without falling back to ad hoc curl calls or undocumented UI endpoints. The repo also needs a committed, reviewable copy of the official n8n public API contract so the utility and its docs can stay aligned with upstream as n8n evolves.

## What Changes

- Add a new repo-owned `ghostship-n8n` CLI utility package for n8n.
- Support every operation in the official n8n public API with dedicated snake_case client methods and CLI commands.
- Mirror the bundled official n8n public OpenAPI document into `docs/api/` and add a canonical Markdown reference sheet for the utility.
- Wire `ghostship-n8n` through the repo's normal package outputs and Hermes image runtime path.
- Document the utility's authentication, pagination, coverage model, and upstream version/source in repo docs.

## Capabilities

### New Capabilities
- `n8n-cli`: Provide a first-class `ghostship-n8n` utility that covers the full official n8n public API, follows the shared Ghostship CLI contract, and ships with committed upstream API documentation artifacts.

### Modified Capabilities

## Impact

- Adds a new Python CLI package under `packages/`
- Adds a new OpenAPI mirror and Markdown reference under `docs/api/`
- Updates flake/image package wiring so the utility is available in the Hermes runtime
- Introduces n8n-specific environment and auth handling for API key access
- Grounds the change on the downloaded bundled upstream spec at `openspec/changes/add-ghostship-n8n-cli/references/n8n-openapi-bundled.yml`
