## Why

The repo already ships `codex` as persisted user-layer tooling rather than as a baked image binary, and `gemini-cli` needs to follow that same model. Restoring Gemini CLI through the managed runtime tooling flow gives operators and Hermes sessions the command by default without reopening the old immutable-image or seeded-workstation contract.

## What Changes

- Add `@google/gemini-cli` to the managed persisted npm tooling contract so `gemini` is installed alongside `codex` and `opencode` under the Hermes user layer.
- Keep `gemini-cli` out of the immutable image-layer CLI exception set, while continuing to rely on managed `nodejs_22` from the Hermes-user Nix profile as the runtime dependency.
- Update runtime docs and validation so the current contract says `gemini` is provided by the managed npm tooling flow rather than by image seeding or the immutable image.
- Preserve the existing Gemini API-backed auxiliary-task provider wiring and `GOOGLE_AI_STUDIO_API_KEY` runtime env contract.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `agent-workstation-runtime`: broaden the normal managed layered-toolchain contract so `gemini` is treated as a supported runtime command from the managed persisted npm tool prefix.
- `agent-workstation-updates`: broaden the managed user-tooling refresh contract so Gemini CLI is installed and refreshed with the same persisted npm workflow as `codex` and `opencode`.

## Impact

- Affected code: `packages/hermes-image/nixos-module.nix` and Hermes image validation coverage for the managed npm toolchain.
- Affected docs: `README.md` and any current runtime documentation that enumerates the managed tool inventory.
- Affected systems: managed user-tooling convergence, the persisted npm tool project under `/home/hermes/.hermes/hermes-agent`, Hermes-user PATH behavior, and runtime smoke validation for supported CLI entrypoints.
- Unchanged systems: immutable default-image CLI policy, managed user Nix profile inventory outside the existing Node runtime dependency, runtime seeding policy, and Gemini auxiliary model/provider configuration.
