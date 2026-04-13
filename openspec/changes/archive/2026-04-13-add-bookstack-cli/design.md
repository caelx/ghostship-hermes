## Context

Ghostship utility packages follow two broad patterns today: small hand-written task wrappers for narrow APIs and generated-style full-surface wrappers that expose one command per upstream operation plus a generic escape hatch. BookStack fits the second category, but its official REST API combines JSON CRUD, multipart uploads, and binary download/export endpoints, which means the existing JSON-first full-surface pattern is not sufficient to deliver honest full coverage.

The proposal is grounded in a captured upstream reference snapshot at `openspec/changes/add-bookstack-cli/references/bookstack-api-docs.html`, taken from the official BookStack demo instance `https://demo.bookstackapp.com/api/docs` on 2026-04-12. That snapshot shows current endpoint groups for pages, chapters, books, shelves, attachments, comments, content permissions, image gallery, imports, recycle bin, roles, search, system, users, and docs, plus BookStack's API token auth and form-data rules.

## Goals / Non-Goals

**Goals:**
- Add a new `ghostship-bookstack` package that follows repo-standard packaging, test, and CLI conventions.
- Capture BookStack's official API docs into repo-owned artifacts so the utility surface is tied to a committed upstream snapshot.
- Support the full upstream BookStack API surface, including multipart upload operations and binary response endpoints.
- Keep the shared CLI contract coherent so future full-surface utilities can reuse the richer HTTP handling instead of hand-rolling special cases.

**Non-Goals:**
- Implement BookStack server extensions, plugins, or internal Artisan/PHP CLI workflows.
- Build a high-level opinionated content-management UX on top of BookStack; this change is about faithful API coverage.
- Guarantee automatic OpenAPI generation from BookStack's docs; if upstream does not expose a stable OpenAPI artifact, the repo will maintain a normalized mirror plus Markdown reference instead.

## Decisions

### Decision: Model BookStack as a full-surface utility package
`ghostship-bookstack` will use the same operation-catalog pattern as the repo's larger API wrappers. The CLI will expose one snake_case command per upstream operation, plus a generic `request` escape hatch. This keeps the command surface aligned with the API contract and avoids opinionated aliases.

Alternatives considered:
- Hand-write a narrower set of task-oriented commands. Rejected because the user explicitly wants the full API and the repo's conventions favor operation-aligned command names.
- Expose only a generic passthrough request command. Rejected because it would not meet the repo's “same as the other utilities” standard.

### Decision: Capture and commit BookStack docs as repo-owned source material
Implementation will pull the official docs from a live BookStack instance and commit canonical artifacts under `docs/api/`. At minimum this includes a Markdown reference sheet. If a stable machine-readable export can be derived from the official docs surface, that normalized snapshot will also be committed beside the Markdown reference.

Alternatives considered:
- Rely on the live `/api/docs` page at runtime. Rejected because repo utilities need a committed contract for drift detection and review.
- Claim an OpenAPI mirror without confirming the format. Rejected because the current official docs surface does not obviously expose a stable OpenAPI artifact.

### Decision: Extend the shared CLI contract instead of special-casing BookStack uploads/downloads
The shared `ghostship-cli-contract` already has low-level request-spec support for `form_data` and `files`, but the generic full-surface CLI pattern only exposes JSON-oriented flags and JSON response assumptions. This change will add shared helpers and command conventions for multipart fields/file attachments and for endpoints that return binary payloads instead of JSON. BookStack will be the first consumer, but the capability is intentionally repo-wide.

Alternatives considered:
- Special-case multipart and binary handling only inside `ghostship-bookstack`. Rejected because that would duplicate logic and leave the shared full-surface contract misleadingly incomplete.
- Downgrade BookStack to partial coverage. Rejected because it conflicts with the stated goal and with the API breadth visible in the captured docs.

### Decision: Separate metadata operations from binary-content fetch operations
JSON endpoints will continue to use the standard request/response path. Binary endpoints such as exports and image-data fetches will need explicit client methods and CLI commands that either emit metadata JSON about the transfer target or write content to disk while still honoring the repo's JSON-first output contract.

Alternatives considered:
- Force binary responses through `request_json()`. Rejected because it would fail on valid non-JSON endpoints.
- Exclude export/data endpoints from “full API”. Rejected because these are first-class upstream operations.

## Risks / Trade-offs

- [BookStack docs format changes or lacks a clean machine-readable export] → Commit the captured upstream HTML snapshot as proposal-time evidence, create a repo-owned Markdown reference, and generate a normalized operation catalog from the verified surface rather than depending on an undocumented format.
- [Shared contract changes ripple into other utilities] → Keep the new multipart/binary helpers additive and preserve existing JSON command behavior for current packages.
- [Binary endpoint UX conflicts with JSON-only defaults] → Define explicit output semantics for binary commands, such as writing to a user-specified path and returning JSON metadata about the action.
- [Multipart encoding details differ between JSON and form submissions] → Capture BookStack-specific rules in the BookStack docs reference and cover upload request builders with focused tests.

## Migration Plan

1. Capture the official BookStack docs into repo-owned API artifacts under `docs/api/` and preserve the proposal-time reference snapshot for traceability.
2. Add shared CLI contract support for multipart/file parameters and binary response handling without breaking current utility behavior.
3. Scaffold `packages/bookstack-cli` with operation catalog, client, CLI, packaging, and tests.
4. Validate the generated operation inventory against the committed BookStack docs snapshot and document any unsupported or intentionally deferred edge cases before merge.

## Open Questions

- Whether BookStack exposes a stable docs JSON or similar export that is reliable enough to commit directly, or whether the repo should maintain its own normalized mirror.
- The exact CLI UX for binary endpoints: whether to require `--output` for all binary fetch/export operations or allow stdout in selected cases.
- Whether any existing full-surface utilities should be opportunistically migrated onto the richer shared multipart/binary helpers during this change or only after `ghostship-bookstack` lands.
