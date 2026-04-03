## Why

The Hermes image already ships curated operator tooling, but it does not yet provide an official password-vault client that an agent can use to receive shared credentials. Adding Bitwarden's supported CLI and a repo-managed usage skill gives the container a documented, stateless secret-retrieval path that fits the repo's noninteractive, JSON-first operating model.

## What Changes

- Add the official `bw` Bitwarden CLI to the Hermes image as a repo-managed Nix package so it is available directly on `PATH`.
- Define the repo's Bitwarden usage contract around environment-variable-driven, noninteractive login and unlock flows instead of interactive session handling.
- Add a repo-managed Bitwarden skill that teaches agents how to authenticate with `BW_CLIENTID`, `BW_CLIENTSECRET`, `BW_PASSWORD`, `BITWARDENCLI_APPDATA_DIR`, and `BW_SESSION`, and how to sync and fetch shared credentials safely.
- Update image/runtime documentation to explain how a dedicated Bitwarden account and shared collections should be used from Hermes.

## Capabilities

### New Capabilities
- `bitwarden-cli-runtime`: Ship the official Bitwarden CLI in the Hermes image and keep it covered by the repo's normal flake and image evaluation.
- `bitwarden-cli-skill`: Seed a repo-managed Bitwarden skill that standardizes the stateless environment-variable workflow for login, unlock, sync, and shared secret retrieval.

### Modified Capabilities

## Impact

- `flake.nix` package wiring and image dependency evaluation
- `packages/hermes-image/` image composition and any runtime conventions needed for Bitwarden CLI state
- `skills/` default seeded skill inventory
- Container/runtime documentation in `README.md`, `CHANGELOG.md`, and related support docs
- Agent secret-sharing workflows that rely on a dedicated Bitwarden account and shared collections
