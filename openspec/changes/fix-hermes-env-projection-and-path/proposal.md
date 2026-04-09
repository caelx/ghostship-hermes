## Why

The current Hermes image has a contract gap between the intended runtime behavior and the live container behavior. Fast-moving user CLIs such as `codex` are installed under `/home/hermes/.local/bin`, but that location is not part of the Hermes user's default path contract everywhere operators expect it, and profile `.env` files are missing Discord variables even when those values are present on the container.

This matters now because the image explicitly treats each profile `.env` as the operator-facing source of truth, and the current bootstrap projection leaves messaging configuration outside that contract. The result is misleading `hermes doctor` output, gateway warnings about missing messaging platforms, and a mismatch between the documented runtime surface and the live profile state.

## What Changes

- Make `/home/hermes/.local/bin` part of the default Hermes user command-discovery contract, not just an ad hoc wrapper path.
- Ensure bootstrap projects the full supported operator-facing env surface into each managed profile `.env`, including the shared and per-profile Discord variables.
- Tighten the managed runtime contract so profile `.env` remains the single operator-facing source of truth for supported profile-facing configuration.
- Update docs and validation expectations so PATH and projected profile env behavior are described and testable in the same way the image actually runs.

## Capabilities

### New Capabilities
- `hermes-profile-env-contract`: Defines the managed profile `.env` projection contract for supported operator-facing configuration, including Discord and other profile-facing runtime inputs.

### Modified Capabilities
- `agent-workstation-runtime`: Clarify that the Hermes runtime user and managed invocation paths SHALL discover supported user-installed tools from `/home/hermes/.local/bin` as part of the normal runtime contract.
- `agent-workstation-updates`: Clarify that supported doctor-facing runtime wiring SHALL include projected profile env for supported profile-facing integrations, so avoidable warnings are not caused by missing bootstrap env projection.

## Impact

- Affected code: `packages/hermes-image/nixos-module.nix`, runtime env/bootstrap wiring, and any related validation helpers.
- Affected docs: `README.md` and any operator-facing guidance that describes the Hermes runtime PATH or the profile `.env` contract.
- Affected behavior: Hermes user command discovery, per-profile `.env` generation, Discord gateway readiness, and doctor output for supported features.
