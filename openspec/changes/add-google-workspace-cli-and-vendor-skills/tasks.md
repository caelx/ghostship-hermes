## 1. Flake and package integration

- [x] 1.1 Add a pinned `googleworkspace/cli` flake input to the repo flake and expose the upstream `gws` package through local outputs.
- [x] 1.2 Wire the packaged `gws` binary into the Hermes image contents and keep flake evaluation/check coverage for the new package path.
- [x] 1.3 Decide and document the repo location that will hold the vendored Google Workspace skill snapshot so updates stay tied to the pinned flake revision.

## 2. Vendor the Google Workspace skills

- [x] 2.1 Import the full upstream Google Workspace skill catalog into the chosen repo-managed vendor path as committed content.
- [x] 2.2 Ensure the vendored snapshot includes the broad upstream skill sets needed for `gws-*`, persona, and recipe workflows without renaming upstream skill directories.
- [x] 2.3 Record the upstream revision/version used for the vendored skill snapshot so maintainers can refresh the CLI and skills together.

## 3. Runtime skill seeding

- [x] 3.1 Update the default skill tree assembly so vendored Google Workspace skills and existing repo-managed local skills are both present in the seeded source tree.
- [x] 3.2 Verify runtime skill seeding still copies only missing directories into `~/.hermes/skills` and preserves any existing user-managed skill content.
- [x] 3.3 Verify a fresh Hermes profile receives both the local runtime/container skills and the vendored Google Workspace skills.

## 4. Flake-first Nix guidance and docs

- [x] 4.1 Rewrite the existing `hermes-nix` skill to make flake-native commands the default guidance for repo and image work.
- [x] 4.2 Update README and related docs to describe the `gws` integration, the vendored broad skill set, and the flake-managed update path.
- [x] 4.3 Document Google account authentication guidance for a dedicated agent account, including narrow-scope Gmail guidance for personal testing-mode apps.

## 5. Verification and release hygiene

- [x] 5.1 Run the relevant flake evaluation/build verification for the new `gws` input and Hermes image wiring.
- [x] 5.2 Confirm the final change includes proposal, design, specs, and docs that match the implemented integration.
- [x] 5.3 Update changelog/versioning as warranted by the final implementation scope before release.
