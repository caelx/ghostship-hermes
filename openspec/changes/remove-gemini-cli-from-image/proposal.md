## Why

The Hermes image still treats Gemini CLI as a managed runtime tool even though the intended operator workflow has narrowed to Codex and OpenCode. That leaves the image, docs, and current OpenSpec contract advertising an agent CLI that maintainers no longer want to install or rely on.

## What Changes

- Remove `@google/gemini-cli` from the Hermes image's managed npm toolchain.
- Remove the managed `gemini` binary from the documented runtime PATH contract.
- Update current runtime and seeding documentation so they describe Gemini only where the repo still intentionally uses Google's API-backed auxiliary model path, not as an installed CLI.
- Keep the existing Gemini auxiliary-task provider wiring and `GOOGLE_AI_STUDIO_API_KEY` contract unchanged.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `agent-workstation-runtime`: Narrow the managed layered toolchain contract so it no longer includes Gemini CLI as a supported installed runtime command.
- `agent-workstation-seeding`: Remove Gemini CLI from the live seeded develop-environment description so fresh state no longer documents it as part of the curated workstation defaults.

## Impact

- Affected code: `packages/hermes-image/nixos-module.nix`
- Affected docs: `README.md`, `AGENTS.md`, and other current repo documentation that describes installed managed CLIs
- Affected specs: `openspec/specs/agent-workstation-runtime/spec.md`, `openspec/specs/agent-workstation-seeding/spec.md`
- Unchanged systems: Hermes auxiliary Gemini provider wiring, `GOOGLE_AI_STUDIO_API_KEY`, and any non-CLI Gemini API usage
