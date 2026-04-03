## Context

The Hermes image already bundles a mix of direct upstream operator tools and repo-owned `ghostship-*` service CLIs, with seeded skills copied into `~/.hermes/skills` on first start. The current Bitwarden integration is built around the Password Manager CLI `bw`, a persisted `BITWARDENCLI_APPDATA_DIR`, and a skill that teaches API-key login, vault unlock, shared collections, and `BW_SESSION`-driven retrieval.

That model does not fit the next service integration. `changedetection.io` is a normal service API that should be automated through a full `ghostship-*` wrapper, while the credentials that Hermes needs for it should come from Bitwarden Secrets Manager instead of a human vault session. This makes the change cross-cutting: it replaces one official Bitwarden product/CLI with another, changes the seeded secret-retrieval workflow, adds a new full-coverage service client package, and introduces a stable upstream OpenAPI artifact into the repo’s API reference inventory.

## Goals / Non-Goals

**Goals:**
- Replace the packaged Bitwarden Password Manager CLI with the packaged Bitwarden Secrets Manager CLI `bws`.
- Standardize a Hermes-managed persisted `bws` config/state location under `HERMES_HOME` instead of relying on default host-oriented paths.
- Replace the current seeded Bitwarden skill content so it teaches the official access-token-based Secrets Manager flow.
- Add a full-coverage `ghostship-changedetection` package that follows the same style as the existing service CLIs: typed client, Typer command surface, JSON-first output, `--timeout`, and `--dry-run` for write/delete operations.
- Persist a stable upstream `changedetection.io` OpenAPI snapshot in `docs/api/` and add the companion Markdown reference sheet.
- Add a repo-managed `changedetection` skill using `skill-creator` guidance, with workflows that start from `bws` secret retrieval and move into `ghostship-changedetection`.

**Non-Goals:**
- Support both `bw` and `bws` in parallel as first-class image tools.
- Keep Password Manager vault login, unlock, shared-collection, or `BW_SESSION` workflows as supported guidance.
- Scope `ghostship-changedetection` down to a partial v1 surface; it must cover the full stable upstream API contract.
- Persist a deployment-specific `changedetection.io` live `/api/v1/full-spec` snapshot in the repo.
- Build a generic Bitwarden wrapper around `bws`; the image should expose the official upstream CLI directly on `PATH`.

## Decisions

### Replace `bw` with `bws` as the bundled Bitwarden contract

The image should stop treating Bitwarden Password Manager as the supported integration and instead package `bws` directly from nixpkgs in the same image/tool wiring that currently exposes `bw`.

Why:
- The operator workflow is moving from vault-account sharing to machine-account secret retrieval.
- Pinned nixpkgs already provides `bws`, so the repo can keep the same reproducible packaging model it uses for other bundled tools.
- Keeping both CLIs in the image would blur the supported path and keep old guidance alive longer than necessary.

Alternatives considered:
- Keep `bw` and add `bws` alongside it. Rejected because it weakens the migration and leaves two conflicting Bitwarden operating models in the same image.
- Install `bws` at runtime from upstream binaries. Rejected because it bypasses the repo’s flake-managed image composition and weakens reproducibility.

### Persist `bws` configuration under Hermes-managed state

The runtime and docs should standardize a persisted `bws` configuration/state path under `HERMES_HOME`, rather than relying on the upstream default under `~/.config`.

Why:
- The container’s safe persisted state is centered on `~/.hermes`, not on every host-style XDG path under the home directory.
- Keeping the `bws` state under `HERMES_HOME` makes the integration compatible with the repo’s existing profile-scoped persistence model.
- A repo-managed path keeps future live-test and documentation flows deterministic.

Alternatives considered:
- Leave `bws` on its upstream default path. Rejected because it would place important config outside the repo’s declared persistence model.
- Store no local `bws` state at all. Rejected because the official CLI supports persisted local configuration and the repo should define where that state belongs.

### Keep the existing repo Bitwarden capability boundary, but rewrite it for Secrets Manager

The repo should continue to treat Bitwarden as a bundled upstream tool plus a seeded local skill, but the skill and docs should now describe `BWS_ACCESS_TOKEN`-driven Secrets Manager workflows and project-scoped secret retrieval instead of Password Manager vault operations.

Why:
- The user asked to replace the existing Bitwarden integration, not to add a second parallel secret system.
- Preserving the repo’s current “bundled tool plus seeded skill” shape limits churn in image composition and skill seeding.
- The meaningful behavioral change is the operating contract, not the existence of a Bitwarden integration itself.

Alternatives considered:
- Drop the Bitwarden skill entirely and document `bws` only in `README.md`. Rejected because the seeded skill is the most reliable place to teach agents the official workflow.
- Introduce a separate `bitwarden-secrets` repo capability and keep the old one. Rejected because the request is a replacement, not a dual-stack migration.

### Generate `ghostship-changedetection` from the stable upstream API contract, but expose repo-style snake_case commands

`ghostship-changedetection` should be implemented as a normal service package under `packages/changedetection-cli/`, with dedicated client methods and CLI commands derived from the stable upstream API semantics and normalized into the same snake_case naming style as the other service CLIs.

Why:
- The repo requirement is full API coverage with the same user-facing style as the other utilities.
- A typed client plus Typer command layer matches the existing package pattern and allows consistent `--dry-run` request rendering.
- Deriving names from endpoint/resource semantics avoids awkward raw upstream naming without sacrificing full coverage.

Alternatives considered:
- Expose only a generic `request` command. Rejected because the user explicitly requires full API coverage in the same style as the existing CLIs.
- Mirror upstream operation IDs verbatim. Rejected because consistency with existing snake_case Ghostship commands is a stronger repo invariant.

### Persist a stable upstream changedetection OpenAPI snapshot as the canonical raw API artifact

The repo should store a stable upstream `changedetection.io` OpenAPI snapshot in `docs/api/changedetection-openapi.json` and pair it with a repo-owned Markdown reference sheet in `docs/api/changedetection.md`.

Why:
- The repo already treats `docs/api/` as the canonical API reference area for each utility.
- The user explicitly wants the API spec persisted, but wants a stable upstream source of truth rather than a deployment-specific merged spec.
- The raw spec plus Markdown sheet model matches the repo’s existing OpenAPI-backed service integrations.

Alternatives considered:
- Persist the live `/api/v1/full-spec` from a running instance. Rejected because it is deployment-specific and would drift from the stable upstream contract.
- Keep only the Markdown sheet. Rejected because the user explicitly wants the upstream API spec artifact persisted too.

### Add a dedicated `changedetection` skill that starts from secrets retrieval and then follows inspect -> dry-run -> mutate -> verify

The repo should seed a short workflow skill under `skills/changedetection/`, written with `skill-creator` guidance, that teaches Hermes to retrieve `changedetection.io` credentials through `bws`, inspect current state with read commands, use `--dry-run` on write/delete operations, and verify post-state with dedicated reads.

Why:
- The repo keeps service skills short, trigger-rich, and workflow-oriented rather than trying to duplicate the full API surface.
- `changedetection.io` is a good example of a service where the operational sequence matters more than memorizing every endpoint.
- The user explicitly reminded the repo to use the same style and format as the other utilities, and the existing service skills follow this pattern.

Alternatives considered:
- Rely on the CLI README and API docs alone. Rejected because seeded skills are how Hermes actually learns the intended workflow.
- Put changedetection guidance inside the Bitwarden skill. Rejected because secret retrieval and service operation are separate triggers and should remain separate skills.

## Risks / Trade-offs

- [Breaking the current `bw`-based workflow] -> Make the runtime, docs, and seeded skill all move together so the new supported path is internally consistent.
- [`bws` persistence details differ from `bw` appdata expectations] -> Define one Hermes-managed location explicitly and verify the runtime creates it the same way it creates other persisted state directories.
- [Full changedetection API coverage creates a large command surface] -> Use the stable upstream OpenAPI snapshot as the inventory source and keep naming generation disciplined around resource semantics and the shared CLI contract.
- [The upstream changedetection schema can be broader than the repo’s manually curated CLIs so far] -> Preserve `request` as the escape hatch, but require dedicated wrappers for every stable upstream operation before the change is complete.
- [Service skill drift from the real CLI surface] -> Author the skill after the CLI command inventory is known and keep it workflow-oriented instead of enumerating the entire API.

## Migration Plan

1. Replace `bw` with `bws` in the flake outputs, dev shell, and image bundle, then update the runtime environment and docs to use a Hermes-managed `bws` state path.
2. Rewrite the repo-managed Bitwarden skill and docs so the supported workflow is Secrets Manager access-token retrieval instead of Password Manager vault sessions.
3. Add `packages/changedetection-cli/` with full stable-upstream API coverage, tests, flake wiring, and image bundling.
4. Persist the stable upstream OpenAPI artifact in `docs/api/`, add the Markdown API reference, and update the API coverage index.
5. Add the `changedetection` skill with `skill-creator` guidance and document the `bws` -> `ghostship-changedetection` workflow in README and changelog entries.
6. Verify the updated flake outputs, package tests, and image/runtime wiring, then remove outdated `bw`-specific references.

Rollback strategy:
- Revert the `bws` packaging/runtime changes together with the Bitwarden skill rewrite and remove the new changedetection package/docs/skill so the image returns to the pre-change contract cleanly.

## Open Questions

- Which stable upstream source file or release artifact should be treated as the canonical `changedetection-openapi.json` snapshot when upstream offers both source-tree and generated-doc variants?
- Whether the changedetection command inventory should group some low-level endpoints under broader resource verbs when the upstream schema exposes multiple near-duplicate operation names for the same resource family.
