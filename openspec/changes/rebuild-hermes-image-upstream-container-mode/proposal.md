## Why

The image had grown into a Ghostship-managed workstation with too much custom runtime logic, seeded skills, vendored assets, and preinstalled coding-agent tooling. The goal of this change is still to strip that back to a lean Hermes image, but the persistence model has now changed again: instead of a split `/data` plus `/data/home` contract, the operator wants the entire `/home/hermes` tree to be the persisted volume.

That keeps the image operationally simpler, makes later-installed tool state persistence automatic, and makes Hermes profile inspection easier because both the managed default state and named profiles live under the same home volume.

## What Changes

- Rebuild the Hermes image around the upstream Hermes flake and NixOS module rather than the legacy Ghostship workstation runtime.
- Keep a lean default image:
  - upstream Hermes
  - runtime Nix support
  - `ttyd`
  - `tirith`
  - the minimal dashboard
  - all `ghostship-*` utilities
- Remove Ghostship-managed extras from both the image and repo tree:
  - Codex
  - Gemini CLI
  - Opencode
  - OpenSpec
  - `skills`
  - vendored Google Workspace assets
  - `feed`
  - `honcho-ai`
  - custom skill seeding
  - workstation seed payloads
  - old `rootfs`
  - old profile reconciler and persistent terminal services
- Keep Hermes built-ins untouched.
- Keep the `hermes` runtime user at `3000:3000`.
- Keep the dashboard minimal, but let it:
  - open unlimited on-demand ephemeral `ttyd` sessions
  - add each session as a focused left-rail tab
  - close the active session and remove its tab
  - return to a blank homepage when no sessions remain
  - start browser terminals in `/home/hermes`
- Bootstrap `test` and `coder` Hermes profiles from NixOS-managed startup so the upstream profile layout is inspectable immediately.
- Persist `/home/hermes`, `/workspace`, and `/nix`.
- Validate `nix profile install` persistence and later-installed tool state persistence across container replacement.

## Approved Deviation From Upstream

This change is intentionally close to upstream Hermes, but one explicit repo-approved deviation remains:

- upstream NixOS/container-mode docs assume a separate managed state root and home directory
- this repo now sets `stateDir = "/home/hermes"`
- that means managed Hermes state lives at `/home/hermes/.hermes`
- the whole `/home/hermes` tree is the persisted volume

This deviation is deliberate and should be documented anywhere the runtime contract is described.

## Capabilities

### New Capabilities

- `lean-runtime-package-set`
- `minimal-hermes-dashboard`

### Modified Capabilities

- `agent-workstation-runtime`
- `agent-workstation-home-state`
- `agent-workstation-seeding`
- `agent-workstation-updates`
- `bitwarden-cli-runtime`
- `bitwarden-cli-skill`
- `feed-monitoring`
- `google-workspace-cli-runtime`
- `google-workspace-skills`
- `changedetection-skill`

## Impact

- Affected code:
  - `flake.nix`
  - `packages/hermes-image/*`
  - `packages/feed/*`
  - `packages/honcho-ai/*`
  - `skills/`
  - `vendor/`
  - image/dashboard tests and docs
- Affected systems:
  - image composition
  - runtime persistence contract
  - browser dashboard behavior
  - runtime documentation and tests
- Risks:
  - the persisted whole-home model is a repo-specific deviation from upstream container-mode docs
  - switching from the `/data` split model to a whole-home mount is a breaking persistence change for anyone who followed the newer draft docs
  - persisted `/nix` still needs explicit ownership and daemon-socket validation
