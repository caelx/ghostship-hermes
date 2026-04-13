## Why

The managed Hermes image needs a cleaner split between its default runtime model contract and a Discord channel reserved for Ghostship Router free models. The current config does not provide a supported, operator-friendly way to expose the router as a named manual provider, move fallback to Codex, or guide Discord users back onto router-backed free models after `/model` drift or `/reset`.

## What Changes

- Change the managed Hermes fallback model from the local router alias `agentic` to `openai-codex/gpt-5.4-mini` while keeping the direct `opencode-go/minimax-m2.7` primary lane.
- Keep auxiliary and compression tasks on the existing direct Gemini 3.1 Flash-Lite path.
- Add one named Hermes custom provider, `ghostship-router`, that points at the local router and exposes its live router model ids for manual `/model` selection.
- Add a managed env contract for `GHOSTSHIP_ROUTER_CHANNEL` so the single-agent runtime can designate one Discord channel as the router-only guidance channel.
- Add a supported warning-only Discord guidance path that detects when the configured router channel is not using a `ghostship-router` model and sends a bold remediation message with full `/model custom:ghostship-router:<model>` commands for every currently exposed router model.
- Send the same guidance after `/reset` in that channel so users can immediately restore a free router model for the next session.
- **BREAKING** Retire this feature's dependence on `DISCORD_FREE_RESPONSE_CHANNELS` as the primary contract for the dedicated router-only Discord channel.

## Capabilities

### New Capabilities
- `discord-router-channel-guidance`: warn users in one configured Discord channel when their active session is not using a router-backed free model, and provide copy-paste `/model` commands for the allowed router models.

### Modified Capabilities
- `hermes-profile-env-contract`: project the new router-channel env input into the managed `.env` and retire the dedicated router-channel dependence on `DISCORD_FREE_RESPONSE_CHANNELS`.
- `router-primary-hermes-runtime`: update the managed runtime model contract so the primary lane remains direct OpenCode Go, the fallback lane moves to Codex, and the local router is exposed as a named manual custom provider instead of the configured fallback model.

## Impact

- Affected code: `packages/hermes-image/nixos-module.nix`, managed Hermes config generation, managed env projection, and the repo-owned Discord guidance integration.
- Affected runtime behavior: fallback selection, manual `/model` usage in Discord, and warning behavior in the configured router-only channel.
- Affected docs/tests: runtime env documentation, README model-contract docs, and validation coverage for managed config generation plus Discord guidance behavior.
