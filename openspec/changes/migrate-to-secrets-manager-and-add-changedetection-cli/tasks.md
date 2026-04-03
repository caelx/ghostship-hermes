## 1. Replace the bundled Bitwarden runtime contract

- [x] 1.1 Replace `bw` with nixpkgs `bws` in `flake.nix`, the dev shell, and Hermes image package wiring.
- [x] 1.2 Update the Hermes runtime conventions to use a documented Hermes-managed `bws` configuration/state path under `HERMES_HOME`.
- [x] 1.3 Remove or rewrite outdated `bw`-specific runtime references so the flake outputs, image bundle, and runtime env all describe the new `bws` contract consistently.

## 2. Rewrite the Bitwarden workflow guidance for Secrets Manager

- [x] 2.1 Rewrite the repo-managed Bitwarden skill to teach the official `bws` access-token workflow and remove `bw`/`BW_SESSION` guidance.
- [x] 2.2 Update `README.md`, `CHANGELOG.md`, and any other affected docs from Password Manager shared-collection guidance to Secrets Manager machine-account and project-secret guidance.
- [x] 2.3 Verify the final runtime docs and Bitwarden skill consistently name the supported `bws` environment and persisted state path.

## 3. Add the full `ghostship-changedetection` package

- [x] 3.1 Persist the stable upstream `changedetection.io` OpenAPI snapshot in `docs/api/` and derive the full snake_case command inventory from it.
- [x] 3.2 Create `packages/changedetection-cli/` with the typed client, Typer CLI, README, tests, and Nix package wiring in the same style as the existing `ghostship-*` utilities.
- [x] 3.3 Implement environment-driven auth with `CHANGEDETECTION_URL` and `CHANGEDETECTION_API_KEY`, plus dedicated wrappers for every stable upstream changedetection operation and a generic `request` escape hatch.
- [x] 3.4 Wire `ghostship-changedetection` into the repo flake outputs, dev shell, and Hermes image bundle.

## 4. Add changedetection docs and workflow skill

- [x] 4.1 Add `docs/api/changedetection.md` and update `docs/api/README.md` so the persisted raw spec and repo summary become the canonical changedetection API reference.
- [x] 4.2 Create `skills/changedetection/SKILL.md` using `skill-creator` guidance and keep it aligned with the repo's short workflow-oriented service-skill pattern.
- [x] 4.3 Make the changedetection skill teach the `bws` -> inspect -> `--dry-run` -> mutate -> verify workflow using `ghostship-changedetection`.

## 5. Verify the integration and finish release hygiene

- [x] 5.1 Run the relevant Python utility test/build flow for `packages/changedetection-cli` and the needed flake/image verification for the new `bws` and changedetection wiring.
- [x] 5.2 Verify the bundled CLIs and seeded skills appear correctly in a fresh Hermes runtime/profile and that the documented workflows match the shipped tools.
- [x] 5.3 Confirm the final proposal, design, specs, docs, and changelog/versioning all describe the same migrated secret model and changedetection integration.
