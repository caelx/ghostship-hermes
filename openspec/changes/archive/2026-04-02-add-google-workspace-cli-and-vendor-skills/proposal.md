## Why

The Hermes image already ships curated agent tooling and repo-managed skills, but it does not yet provide a broad Google Workspace operating surface. Adding the Google Workspace CLI and its upstream skill set closes that gap with a JSON-native toolchain that fits the repo contract, while a flake-first integration keeps builds reproducible and consistent with the repo's Nix stance.

## What Changes

- Add the upstream `gws` Google Workspace CLI to the image as a pinned flake-based dependency instead of an ad hoc runtime installer.
- Vendor the full upstream `googleworkspace/cli` skill snapshot into this repo so the image can seed a broad `gws-*`, persona, and recipe skill set offline and reproducibly.
- Extend first-start skill seeding so the vendored Google Workspace skills are copied into `~/.hermes/skills` without overwriting user-managed content.
- Update repo-managed Nix guidance to be explicitly flake-first for image work, tool execution, and user installs.
- Document dedicated Google account authentication guidance for a broad Workspace skill set, including narrow-scope Gmail guidance for testing-mode personal accounts.

## Capabilities

### New Capabilities
- `google-workspace-cli-runtime`: Build and ship the upstream `gws` CLI in the Hermes image through a pinned flake input.
- `google-workspace-skills`: Vendor and seed the upstream Google Workspace skill catalog as part of the repo-managed Hermes default skills.
- `flake-first-nix-guidance`: Provide repo-managed agent guidance that prefers flake-native Nix workflows for package execution, development shells, and image changes.

### Modified Capabilities

## Impact

- `flake.nix` inputs, package wiring, and checks
- `packages/hermes-image/` image composition and default skill seeding behavior
- `skills/` layout and repo-managed skill inventory
- Container/runtime documentation in `README.md` and related support docs
- Authentication guidance for Google Workspace and Gmail usage inside Hermes profiles
