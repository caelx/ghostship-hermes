## Why

The current router policy mixes multiple alias families, treats NVIDIA Build as a tiny curated allowlist, and allows provider failover too eagerly for the user's desired operating mode. That makes the live free-model pool smaller than the real catalog, weakens provider-priority intent, and keeps routing behavior focused on generic bucket heuristics instead of the single agentic workload the repo actually cares about.

## What Changes

- **BREAKING** Remove the multi-alias routing contract and make `agentic` the only repo-supported router alias for normal model selection.
- **BREAKING** Replace the repo-curated NVIDIA Build allowlist with live NVIDIA catalog discovery, while still filtering to free endpoints and supporting durable ranked/unused overrides.
- Rework router ranking so the primary decision is a repo-owned static usable-model policy supplied for the currently known free models. Newly discovered models are not routed until they are manually categorized.
- Rework provider routing policy so `nvidia-build` always outranks `opencode-zen`, which always outranks `openrouter`, and cross-provider failover only happens after the active provider is clearly exhausted for free usage instead of after ordinary retryable model failures.
- Add smarter daily-limit exhaustion inference so the router can classify likely per-day free-tier exhaustion from provider-specific signals, repeated pacing, and repeated zero-output failures even when an upstream provider does not expose a clean daily-limit API.
- Preserve model-level retry and cooldown behavior inside a provider so the router can keep trying lower-ranked models from the same provider before abandoning that provider.
- Keep provider and session stickiness so the `agentic` lane behaves consistently over time instead of flapping between candidates.
- Update the managed runtime and Discord forced-channel contracts so the repo-owned `ghostship-router` path uses `agentic` instead of `coding`.
- Update validation and observability so maintainers can prove which provider was selected, why a provider stayed active or was abandoned, and whether a provider switch happened because of explicit free-tier exhaustion evidence.
- Add a single repo-owned policy surface for the supplied top-five usable models per provider, explicit unused-model lists, provider-specific exhaustion rules, and recovery thresholds so future catalog refreshes do not require ad hoc code edits across provider code.
- Add operator-facing inventory surfaces that list uncategorized discovered models and discovered models that were explicitly marked unused so ranking maintenance stays manual and visible.
- Seed the initial per-provider top-five usable ranking from the supplied Hermes-weighted ranking:
  - `nvidia-build`: `minimaxai/minimax-m2.7`, `qwen/qwen3-coder-480b-a35b-instruct`, `moonshotai/kimi-k2-thinking`, `deepseek-ai/deepseek-v3.2`, `z-ai/glm-4.7`
  - `opencode-zen`: `big-pickle`, `minimax-m2.5-free`, `trinity-large-preview-free`, `nemotron-3-super-free`, `gpt-5-nano`
  - `openrouter`: `qwen/qwen3-next-80b-a3b-instruct:free`, `google/gemma-4-31b-it:free`, `google/gemma-4-26b-a4b-it:free`, `openai/gpt-oss-120b:free`, `meta-llama/llama-3.3-70b-instruct:free`
  - normal routing still uses only the best three currently eligible models from each provider's top five

## Capabilities

### New Capabilities
- None.

### Modified Capabilities
- `model-router-service`: Change NVIDIA inventory policy to catalog discovery, collapse normal routing to the `agentic` alias, replace generic shortlist-first selection with explicit per-provider usable rankings, keep a top-five ranked reserve per provider while routing only across the best three currently eligible models from that five-model set, expose uncategorized and unused discovered-model inventories, and require provider-ordered failover only after clear free-tier exhaustion, including inferred daily-limit exhaustion.
- `router-primary-hermes-runtime`: Change the managed `ghostship-router` custom-provider contract from `coding` to `agentic` and update validation around the repo-supported router alias.
- `discord-free-channel-router`: Change the managed Discord forced-response route from router alias `coding` to router alias `agentic`.

## Impact

- Affected code: `packages/hermes-router`, managed image/runtime wiring, Discord forced-channel integration, router tests, and image validation.
- Affected systems: NVIDIA Build inventory refresh, provider selection, model ranking, session stickiness, exhaustion/cooldown handling, daily-limit inference, operator inventory surfaces, managed Hermes custom-provider config, and Discord pinned-response routing.
- Affected operator inputs: explicit per-provider top-five usable rankings, explicit unused-model lists, provider-specific exhaustion policy, and the repo-owned router policy file that controls discovery and recovery behavior.
