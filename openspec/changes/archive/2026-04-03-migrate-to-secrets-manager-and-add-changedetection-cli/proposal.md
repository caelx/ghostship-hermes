## Why

The current image secret workflow is built around the Bitwarden Password Manager CLI `bw`, shared collections, and vault unlock sessions, but the next Hermes integration needs machine-account secret access that fits Bitwarden Secrets Manager instead. At the same time, Hermes needs first-class automation for `changedetection.io`, including a full repo-managed CLI surface and a stable upstream API spec snapshot that can be carried in the repo like the other service integrations.

## What Changes

- **BREAKING** Replace the bundled Bitwarden Password Manager CLI workflow with Bitwarden Secrets Manager by packaging `bws`, removing the `bw`-specific runtime assumptions, and documenting Hermes-side persisted `bws` state under `~/.hermes`.
- **BREAKING** Replace the seeded Bitwarden skill content so it teaches the official Secrets Manager machine-account workflow with access tokens and project-scoped secrets instead of Password Manager login, unlock, shared collections, and `BW_SESSION`.
- Add a new full-coverage `ghostship-changedetection` utility that follows the existing repo contract: dedicated snake_case commands for the stable upstream API, JSON-first output, `--timeout` on every invocation, and `--dry-run` on write/delete paths.
- Persist the stable upstream `changedetection.io` OpenAPI snapshot in `docs/api/` and add the canonical Markdown API reference that explains auth, endpoint groups, and utility coverage.
- Add a repo-managed `changedetection` skill, authored with `skill-creator` guidance, that teaches Hermes how to retrieve changedetection credentials from Bitwarden Secrets Manager and operate the service with `ghostship-changedetection`.
- Update flake wiring, image composition, runtime conventions, README, changelog, and related docs so the new secrets model and changedetection integration are the documented path.

## Capabilities

### New Capabilities
- `changedetection-cli`: Provide a full stable-upstream `changedetection.io` API utility, persist the upstream OpenAPI snapshot in `docs/api/`, and document the JSON-first CLI contract.
- `changedetection-skill`: Seed a repo-managed Hermes skill that uses Bitwarden Secrets Manager plus `ghostship-changedetection` for changedetection inspection and mutation workflows.

### Modified Capabilities
- `bitwarden-cli-runtime`: Replace the runtime-packaged Bitwarden Password Manager CLI contract with a Bitwarden Secrets Manager CLI contract and a Hermes-managed persisted `bws` config/state path.
- `bitwarden-cli-skill`: Replace the seeded Bitwarden skill requirements so the official workflow is access-token-based Secrets Manager usage rather than `bw` login, unlock, sync, and shared-collection retrieval.

## Impact

- Affected code: `flake.nix`, `packages/hermes-image/`, `skills/`, `docs/api/`, `README.md`, `CHANGELOG.md`, and a new `packages/changedetection-cli/` package tree with tests
- Affected systems: image tool bundle, Hermes runtime secret conventions, seeded skills, API reference inventory, and Hermes service automation workflows
- Dependencies: nixpkgs `bws`, stable upstream `changedetection.io` OpenAPI source material, and repo skill authoring aligned with `skill-creator`
