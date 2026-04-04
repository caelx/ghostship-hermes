## Why

The Hermes image currently drifts from the repo-managed agent defaults in two places: refreshed OpenSpec overrides still instruct agents to use `.worktree/<name>/`, and the workstation seed still advertises and installs the removed `brainstorming` skill. This leaves regenerated instructions inconsistent with the repo policy and keeps shipping a skill that is no longer part of the curated Hermes setup.

## What Changes

- Update the Hermes runtime OpenSpec override generator so refreshed propose instructions use `.worktrees/<name>/`.
- Remove `brainstorming` from the workstation seed's default agent guidance, Codex skill list, and other repo-managed references.
- Stop shipping the seeded `brainstorming` skill payload as part of the Hermes workstation defaults.
- Keep the change non-destructive for existing persisted homes unless a later migration explicitly opts into cleanup.

## Capabilities

### New Capabilities
<!-- None. -->

### Modified Capabilities
- `agent-workstation-seeding`: The seeded workstation defaults must reflect the current curated skill set and stop referencing removed skills such as `brainstorming`.
- `agent-workstation-updates`: OpenSpec asset refresh must reapply the current Ghostship override text, including the `.worktrees/<name>/` worktree guidance.

## Impact

- Affected code: `packages/hermes-image/runtime.nix`, `packages/hermes-image/workstation-seed/.agents/AGENTS.md`, `packages/hermes-image/workstation-seed/.config/codex/config.toml`, and `packages/hermes-image/workstation-seed/.agents/skills/`.
- Affected runtime behavior: fresh Hermes workstation seeds and OpenSpec refresh output inside the image.
- Operator impact: existing persisted homes may retain previously seeded `brainstorming` content until manually removed or handled by a later migration.
