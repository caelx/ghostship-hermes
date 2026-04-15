## Why

The managed Ghostship Hermes runtime still ships the opposite provider order from the one now desired: direct `opencode-go/minimax-m2.7` primary, `openai-codex/gpt-5.4-mini` fallback, and a separate Discord Codex-pinned channel. That contract now adds unnecessary channel surface and keeps the default runtime on the wrong provider/model stack for the main agent experience.

## What Changes

- **BREAKING** remove the managed Discord Codex-pinned channel contract and its downstream env key `GHOSTSHIP_CODEX_CHANNEL`
- keep the managed Discord forced-channel behavior only for the router-pinned free-response lane
- **BREAKING** flip the managed Hermes runtime model order so the primary lane is `openai-codex/gpt-5.4`
- **BREAKING** change the managed fallback model to direct `opencode-go/minimax-m2.7`
- lower the shared managed agent default `reasoning_effort` from `high` to `medium` so the default Codex lane matches the intended thinking level
- add migration/convergence behavior so persisted homes are updated away from the retired fallback and removed Codex channel contract instead of silently retaining stale config
- update validation and docs to prove and describe the new primary/fallback order and Discord env contract

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `discord-free-channel-router`: remove the Codex-pinned Discord lane and keep only the router-pinned forced-response channel behavior
- `router-primary-hermes-runtime`: change the managed primary model path to Codex `gpt-5.4`, move `opencode-go/minimax-m2.7` to fallback, and set the shared managed reasoning default to `medium`
- `hermes-profile-env-contract`: remove `GHOSTSHIP_CODEX_CHANNEL` from the downstream Discord env contract and update the documented provider/runtime expectations

## Impact

- Affected code: `packages/hermes-image/nixos-module.nix`, `packages/hermes-image/build/init_home.py`, `packages/hermes-image/build/prepare_upstream_hermes.py`, image smoke tests, persistence validation, and dashboard/runtime docs
- Affected systems: managed Hermes bootstrap/config convergence, Discord forced-channel routing, persisted home migration behavior, and runtime contract documentation
- Affected operator contract: downstream Discord deployments stop supplying `GHOSTSHIP_CODEX_CHANNEL`; the main runtime now expects Codex auth and `OPENCODE_GO_API_KEY` for the reversed primary/fallback order
