## Context

This repo already ships multiple repo-owned `ghostship-*` service CLIs that wrap supported upstream APIs behind a shared JSON-first command contract. n8n is a good fit for the same pattern because upstream publishes an official Public API, an official authentication and pagination model, and an official OpenAPI source tree in `n8n-io/n8n`.

The important implementation constraint is that the upstream source spec is composed from many `$ref` files under `packages/cli/src/public-api/v1/handlers/*/spec` and `shared/spec`. The repo therefore needs to mirror a bundled single-file contract for documentation and coverage verification rather than copying only the top-level `openapi.yml` source root. This change already downloaded that bundled contract into `openspec/changes/add-ghostship-n8n-cli/references/n8n-openapi-bundled.yml` for proposal-time grounding.

The user requirement is to support the full official n8n public API in a `ghostship-n8n` utility. That means the utility should target the published public API surface only, not reverse-engineered private UI endpoints or internal controller routes.

## Goals / Non-Goals

**Goals:**
- Add a first-class `ghostship-n8n` utility package that follows the shared Ghostship CLI contract.
- Mirror the official bundled n8n public API contract into `docs/api/` and document it with a repo-owned reference sheet.
- Expose dedicated snake_case client methods and CLI commands for every operation in the mirrored public API contract.
- Support API-key auth, configurable public API path/version, and cursor pagination where upstream uses it.
- Make coverage drift detectable by comparing the mirrored upstream spec to the utility inventory in tests.

**Non-Goals:**
- Support undocumented private n8n UI endpoints.
- Create a Ghostship skill for n8n as part of this change.
- Build speculative wrappers for future upstream API versions beyond the mirrored `v1` contract.

## Decisions

### Scope the utility to the official n8n Public API only
The utility will implement the published n8n Public API contract and no broader internal backend surface. The official docs, auth model, Swagger UI path, and upstream OpenAPI source all point to this public API as the supported integration boundary.

Alternative considered: wrap private UI/backend endpoints used by the editor. Rejected because upstream does not publish a full supported spec for that broader surface, and it would create a brittle maintenance burden outside the user's stated requirement.

### Mirror a bundled upstream contract in repo-normalized form
The repo should commit a single-file bundled upstream spec under `docs/api/` and treat it as the utility's machine-readable source of truth. The implementation can keep the proposal-time YAML bundle in the change directory as a research artifact, but the durable repo artifact should follow the repo's existing `*-openapi.json` naming convention.

Alternative considered: commit only the top-level upstream `openapi.yml`. Rejected because it depends on unresolved relative references and is not the complete standalone contract maintainers need for docs review, drift detection, or code coverage checks.

### Implement one dedicated command per mirrored operation, plus `request` as an escape hatch
`ghostship-n8n` should expose a typed client method and snake_case CLI command for every mirrored public API operation. A generic `request` command can remain for debugging or temporary upstream changes, but it must not be used as a substitute for dedicated coverage.

Alternative considered: implement only high-value endpoint groups and leave the rest to `request`. Rejected because the user explicitly asked for full public API support.

### Use environment-driven base URL, auth, and public API path configuration
The client should read `N8N_URL` and `N8N_API_KEY` as the primary configuration inputs, and it should support optional overrides for the public API path and version so self-hosted instances with non-default endpoint settings remain supported. Requests should always send the upstream-supported `X-N8N-API-KEY` header.

Alternative considered: hardcode `/api/v1` and only accept a single base URL. Rejected because upstream documents a configurable public API endpoint path.

### Enforce spec-to-command coverage in tests
The package tests should compare the mirrored bundled OpenAPI snapshot against the implemented client and CLI inventory so missing wrappers are caught as part of normal package test runs. This is the practical way to keep a 60+ operation CLI honest over time.

Alternative considered: rely on manual command lists in README and ad hoc reviewer checks. Rejected because that will drift as soon as upstream adds or renames operations.

## Risks / Trade-offs

- [Upstream n8n adds or changes public API operations] -> Mirror the bundled upstream spec in repo and use coverage tests that fail when command inventory no longer matches.
- [The command surface becomes large and harder to navigate] -> Group commands by resource family in docs and help output, but keep one dedicated command per operation.
- [Some public API operations are gated by plan, role, or instance state] -> Keep full wrapper coverage, but make live integration tests conditional and use mirrored-spec coverage tests for always-on verification.
- [Self-hosted instances customize the public API path] -> Support explicit client-side path/version overrides and document the defaults clearly.
- [Repo convention prefers JSON raw mirrors while upstream serves YAML] -> Convert the bundled upstream contract into repo-normalized JSON for `docs/api/`, while retaining the downloaded YAML bundle in the change reference folder for traceability.

## Migration Plan

1. Mirror the bundled upstream n8n public API contract into `docs/api/` and write the canonical Markdown reference sheet.
2. Scaffold `packages/n8n-cli` on the shared Ghostship CLI contract with environment-based auth and request plumbing.
3. Implement the mirrored operation inventory in typed client methods and snake_case CLI commands.
4. Add flake/image wiring, command/spec coverage tests, and package verification.
5. Update repo docs and changelog so operators can discover and use `ghostship-n8n` from the default image.

## Open Questions

- Whether the eventual command naming should derive primarily from upstream `operationId` values or from a repo-normalized resource/action map when the upstream names are awkward.
- Whether the implementation should generate part of the client/CLI surface from the mirrored OpenAPI snapshot or keep the surface fully hand-written with coverage tests.
