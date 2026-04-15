## Why

The router currently only discovers OpenRouter and OpenCode Zen, and its provider ordering still favors the existing providers rather than a curated free-only NVIDIA lane. The user wants NVIDIA Build API added as a first-class provider, restricted to a curated free coding set, and ranked ahead of the other providers while keeping per-bucket candidate selection bounded and predictable.

The managed Discord free-response router channel is also pinned to alias `agentic`, but the desired channel behavior is now `coding`. This needs an explicit contract change so the image bootstrap, runtime patching, and validation stop asserting the old lane.

## What Changes

- Add native NVIDIA Build API provider support to `ghostship-router` using an environment-provided API key.
- Restrict the NVIDIA provider to a curated free-only model inventory instead of broad dynamic catalog ingestion.
- Keep at most the top 3 scored models per provider for each router bucket before cross-provider interleaving and final candidate selection.
- Raise NVIDIA provider priority above the other router providers while still honoring free-only eligibility, health, cooldown, and provider pacing.
- Update router ranking-worker provider preference and candidate normalization so NVIDIA can participate as a first-class provider.
- Change the managed Discord free-response router channel pin from alias `agentic` to alias `coding`.
- Update docs, specs, and validation to reflect the new provider set, provider priority, bucket capping rule, and Discord router-channel lane.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `model-router-service`: Add prioritized NVIDIA Build API provider support, enforce free-only NVIDIA routing, and cap each provider to its top 3 scored candidates per bucket before global routing.
- `discord-free-channel-router`: Change the forced Discord router-channel alias from `agentic` to `coding`.

## Impact

- Affected code: `packages/hermes-router`, `packages/hermes-image/build/init_home.py`, `packages/hermes-image/build/prepare_upstream_hermes.py`, router tests, image smoke validation, and router docs.
- Affected config/env: new NVIDIA provider credential input and router provider-priority defaults.
- Affected systems: local router inventory refresh, candidate ranking, ranking-worker selection, Discord forced-channel routing, and image/runtime contract documentation.
