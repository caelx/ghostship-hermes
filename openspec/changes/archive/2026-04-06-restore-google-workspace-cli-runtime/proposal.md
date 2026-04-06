## Why

The repo currently has drift between the intended Google Workspace runtime and the active image policy: the live CLI spec still expects `gws`, the live skills spec still expects vendored Google Workspace skills, and the current image/docs ship neither. This change restores the useful part of that integration now by bringing back the pinned `gws` CLI while explicitly excluding all Google Workspace skills.

## What Changes

- Restore the upstream `gws` executable as a pinned flake-provided package in the default Hermes image so it is available on `PATH` automatically.
- Reconnect repo package and image evaluation so `gws` integration failures surface through normal flake inspection and build workflows.
- Remove Google Workspace skill vendoring and first-start skill seeding from the active integration contract.
- Update repo guidance and user-facing docs to describe Google Workspace support as CLI-only.

## Capabilities

### New Capabilities
- None.

### Modified Capabilities
- `google-workspace-cli-runtime`: tighten the default-image contract around a pinned, automatically available `gws` executable.
- `google-workspace-skills`: replace vendoring and runtime seeding requirements with an explicit no-skills contract.

## Impact

- `flake.nix` and image package wiring that determine which tools ship on the runtime `PATH`
- Google Workspace integration specs under `openspec/specs/`
- Runtime and operator guidance in `README.md`, `AGENTS.md`, and `CHANGELOG.md`
