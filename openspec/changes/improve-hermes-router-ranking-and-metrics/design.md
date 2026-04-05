## Context

`packages/hermes-router` already provides the core router service: stable aliases, OpenRouter and OpenCode Zen inventory refresh, model-level failover, SQLite persistence, mixed Zen endpoint-family support, and debug JSON surfaces. What it does not yet provide is a strong operational layer for ranking, provider health, overrides, and metrics.

Today the routing score is still mostly derived from naming heuristics, static tags, and a few last-seen counters. The old router spec expected the service to reason about rolling latency, recent failures, likely free-tier exhaustion, provider-wide health, and ranking over time. The user also wants ranking to use a free model from the `lightweight` bucket rather than a paid or heavyweight path.

This change stays inside the router service itself. The Hermes-facing API remains stable; the work is in background maintenance, state, scoring, and observability.

## Goals / Non-Goals

**Goals:**
- Add a stronger model-ranking layer that combines live health data with background lightweight-model-assisted ranking.
- Keep failover and penalties attached to concrete models while adding provider-wide health and temporary disablement.
- Persist rolling model and provider state needed for unattended routing.
- Add a stable metrics endpoint and richer ranking/health debug views.
- Add durable operator overrides for model/provider weighting, disablement, and alias pinning.
- Keep all ranking and classification work out of the request hot path.

**Non-Goals:**
- Making Hermes use the router by default in this change.
- Reintroducing Gemini fallback.
- Adding streaming response support in this phase.
- Building a browser UI for router administration.
- Replacing the existing alias API contract.

## Decisions

### Add a ranking layer on top of the current heuristic score
The router will keep a deterministic base score from current health and heuristics, then add a persisted learned ranking score and operator weight adjustments. Final candidate ordering becomes the combination of:

- eligibility filters
- provider/model cooldown state
- free-model preference
- alias compatibility
- rolling health score
- learned ranking score
- operator override weight

This avoids making request routing depend entirely on one background model output and gives the system a sane fallback when ranking data is stale or unavailable.

Alternative considered: replacing the current score with model-generated ranking only. Rejected because it makes routing brittle when the ranking worker is unavailable or misclassifies a model.

### Use a healthy free model from the lightweight bucket for background ranking
Background ranking and classification should use a currently healthy free model selected from the `lightweight` pool. The router may allow an override for the worker model, but the default behavior should be “pick the best currently healthy free lightweight model.”

This ranking worker is only used in maintenance jobs, never inline on request routing. The request path continues to use persisted ranking outputs and rolling health data.

Alternative considered: pinning a single hardcoded ranking model. Rejected because it would recreate brittle inventory assumptions and could fail badly when that model disappears or becomes unusable.

### Split ranking into coarse scoring and selective reranking
The router should not send the entire inventory through a heavyweight ranking prompt every refresh. Instead:

1. Generate or update coarse alias-fit scores for the current inventory.
2. Run pairwise or shortlist reranking only for the top candidates in each alias bucket.
3. Persist ranking reason and confidence so the debug surface can explain the result.

This keeps the maintenance cost bounded while still improving model sorting where it matters most.

Alternative considered: pairwise ranking across the full inventory. Rejected because it scales poorly and adds unnecessary maintenance latency and cost.

### Add provider-wide health state beside model-level state
The router already tracks model-level cooldowns and failures. This change will add a separate provider-state table so the service can temporarily suppress entire providers when they show broad auth, timeout, or rate-limit failure patterns.

Provider-wide suppression should remain temporary and should be revisited by refresh or cooldown expiry. Model-level state remains the primary failover mechanism; provider state acts as a coarse guardrail when many models from the same provider fail together.

Alternative considered: inferring provider health only from individual model cooldowns. Rejected because it makes broad provider outages recover too slowly and requires repeated request-path failures before the router adapts.

### Add rolling windows rather than only lifetime counters
The current state model is dominated by lifetime counters and last-seen timings. This change will add rolling-window or decay-based fields for:

- recent successes and failures
- recent timeouts
- recent rate limits
- recent auth failures
- p50 and p95 total latency
- p50 and p95 first-text latency
- recent provider refresh failures

The ranking layer and provider quarantine logic should prefer recent behavior over lifetime totals.

Alternative considered: continuing to rank primarily on total counts. Rejected because long-lived counters adapt too slowly to volatile free-model conditions.

### Expose a stable Prometheus-style metrics endpoint
The router will add `GET /metrics` with Prometheus text exposition. JSON debug endpoints remain useful for operator inspection, but metrics are needed for time-series visibility and tuning.

Initial metrics should cover:

- request counts by alias/provider/model/result
- failover counts
- refresh counts and failures
- active model/provider cooldowns
- request latency histograms
- first-text latency histograms
- candidate counts by alias
- model ranking and health gauges

Alternative considered: relying only on `/debug/*` JSON endpoints. Rejected because they are hard to aggregate and not suitable for continuous monitoring.

### Add durable operator override state in SQLite
The router needs an operational layer beyond env-driven allow/block lists. This change will add durable overrides for:

- force-enable or force-disable a model
- force-enable or force-disable a provider
- manual model and provider weight adjustments
- alias pinning or ordered preferred candidates

Overrides should live in SQLite and be visible through debug surfaces. They remain config-driven in spirit, but no longer require a restart or source edit.

Alternative considered: keeping overrides in env only. Rejected because it is too blunt and makes live operational tuning awkward.

## Risks / Trade-offs

- [Background ranking could drift from real runtime behavior] -> Mitigate by combining it with rolling live health data rather than trusting it directly.
- [Rolling statistics can complicate the SQLite schema] -> Mitigate by adding derived fields incrementally and keeping migration logic straightforward.
- [Provider-wide cooldowns can suppress useful models too aggressively] -> Mitigate with conservative thresholds, short default cooldowns, and clear debug visibility.
- [Metrics can bloat implementation scope] -> Mitigate by starting with a narrow but stable metric set and deferring optional series.
- [Endpoint-family probing in Zen can still add noise to model health] -> Mitigate by persisting learned endpoint family and not reprobing unless a mismatch is observed.

## Migration Plan

1. Extend SQLite schema for rolling model state, provider state, overrides, and ranking outputs.
2. Add provider-state tracking and provider-wide cooldown logic without changing the public API.
3. Add background ranking jobs that select a healthy free lightweight worker and persist ranking outputs.
4. Add `GET /metrics` and richer debug ranking/provider views.
5. Add operator override persistence and expose it through router debug/admin-friendly surfaces.
6. Validate with unit tests, router-local smoke tests, and live refresh/ranking checks against current OpenRouter and OpenCode Zen credentials.

Rollback remains straightforward because the router API stays stable. If the new ranking layer misbehaves, routing can fall back to heuristic-only scoring while retaining the existing request surface.

## Open Questions

- Should provider-level cooldown use a fixed threshold model, a decay-based score, or both?
- Do we want ranking confidence to affect candidate ordering immediately, or only as a tiebreaker until it has enough observations?
- Should operator overrides be exposed through write APIs in this change, or only persisted/readable state plus config wiring?
- How many top candidates per alias should go through selective reranking on each maintenance pass?
