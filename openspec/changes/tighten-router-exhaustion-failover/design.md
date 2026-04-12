## Context

The current router persists model-level and provider-level health in shared rolling counters, but its failure handling is not sequence-aware enough for free-model throttling and account exhaustion. A single retryable failure currently updates both model and provider cooldown state, which can suppress an entire provider after one noisy model response instead of proving that the provider is broadly exhausted.

This change targets the local router in `packages/hermes-router` and the existing `model-router-service` capability. The new behavior must remain transparent to callers within a single request, continue to use the existing ranked priority list, and work across both OpenRouter and OpenCode Zen despite their different exhaustion semantics.

## Goals / Non-Goals

**Goals:**

- Preserve transparent in-request failover while tightening how exhaustion affects model and provider eligibility.
- Introduce an escalating per-model exhaustion cooldown ladder instead of a flat retryable-failure cooldown.
- Detect provider-wide exhaustion from recent distinct-model zero-output failures on the same provider, even when request attempts alternate between providers because of ranking.
- Disable broadly exhausted providers for a longer floor of six hours and re-admit them through probe-style recovery.
- Keep provider-specific rules for OpenRouter free-model throttling and OpenCode Zen balance or limit exhaustion explicit and testable.

**Non-Goals:**

- Changing alias ranking strategy beyond the new cooldown and provider-suppression inputs.
- Changing non-exhaustion failure handling such as plain timeouts, model removal refreshes, or endpoint-family mismatch recovery.
- Exposing provider-specific billing state directly to callers.

## Decisions

### Use a two-layer circuit breaker: model ladder plus provider breaker

The router will separate exhaustion handling into:

- a per-model cooldown ladder for `(provider, backend_model)`
- a provider-wide breaker keyed by recent exhaustion evidence for `provider`

This avoids the current ambiguity where one model failure can effectively act like a provider outage. A model-level exhaustion event updates that model's ladder first, then candidate selection re-enters the normal ranked pool. The provider breaker trips only after stronger evidence of broad provider exhaustion appears.

Alternative considered: continue using only decayed provider counters and thresholds. Rejected because the desired trigger is sequence-sensitive, not just volume-sensitive. The router needs to recognize "distinct models failed with zero output on the same provider inside a short window" as a stronger signal than a raw count of recent failures.

### Recompute candidates from the ranked priority list after every retryable exhaustion failure

After a retryable exhaustion-class failure, the router will:

1. update model or provider state
2. recompute eligible candidates using the existing ranking logic
3. continue with the highest-ranked remaining candidate

The router will not hardcode "same provider first" or "other provider first." This keeps the existing ranking and alias priority behavior intact while allowing cooldowns and provider suppression to influence selection naturally.

Alternative considered: force same-provider fallback before cross-provider fallback. Rejected because the user explicitly wants switching to keep honoring the priority list, and different aliases may legitimately prefer candidates on another provider after a single model cooldown.

### Trip provider-wide disablement only on recent distinct-model zero-output exhaustion evidence

The provider breaker will trip when all of these are true:

- the provider has one recent exhaustion evidence record within a short suspect window
- the current failed backend model is distinct from the previous failed model on that provider
- both failures are exhaustion-class signals
- both failures produced no output

This evidence is provider-scoped, so the breaker still works if the request temporarily switched to another provider between the two failures.

Alternative considered: trip on any two failures from the same provider. Rejected because `model_missing`, endpoint-family mismatch, or partial-output failures do not prove provider-wide exhaustion and would over-disable healthy providers.

### Use provider-specific exhaustion categories

The provider breaker and model ladder will treat these as exhaustion-class events:

- OpenRouter: `429 rate_limited`
- OpenCode Zen: `429 rate_limited`, explicit `insufficient_balance`, and other explicit spend-limit exhaustion if the adapter can classify it

`model_missing`, `endpoint_family_mismatch`, `bad_request`, and ordinary inventory refresh failures will not count toward provider exhaustion evidence.

Alternative considered: treat all retryable failures as exhaustion. Rejected because the resulting cooldown behavior would be too aggressive and would conflate transient transport issues with quota or capacity exhaustion.

### Use an escalating model cooldown ladder and a longer provider disable floor

The exhaustion ladder for each model will be:

- first consecutive exhaustion: `30s`
- second: `1m`
- third: `5m`
- fourth: `10m`
- later events continue escalating with a cap

When broad provider exhaustion is proven, provider disablement will use a minimum floor of `6h`. Recovery after provider disablement will enter probe mode, where one eligible model from that provider may compete again. A failed exhaustion probe re-disables the provider with a longer duration.

Alternative considered: a fixed per-model cooldown or immediate provider disable on the first `429`. Rejected because free-model capacity noise is common enough that the router needs graduated model backoff before concluding the provider is broadly unavailable.

### Make observability expose breaker state explicitly

Debug and metrics surfaces should expose:

- model exhaustion streak and current cooldown
- provider breaker state, disable reason, and cooldown expiry
- whether the provider is in probe mode

This is necessary so operators can distinguish "one hot free model is cooling down" from "OpenRouter was broadly rate-limited and is disabled for six hours."

Alternative considered: infer everything from existing cooldown timestamps. Rejected because probe state and exhaustion evidence sequencing would be opaque and difficult to validate.

## Risks / Trade-offs

- [Provider disablement becomes too sticky for noisy free models] -> Keep the provider breaker dependent on distinct-model zero-output evidence and use probe recovery instead of immediate full re-admission.
- [Ranking and failover become harder to reason about] -> Keep candidate reselection grounded in the existing priority list and expose breaker state in debug and metrics surfaces.
- [Provider-specific parsing drifts from upstream behavior] -> Limit provider-specific branching to well-defined classified categories and cover it with provider adapter tests.
- [Long provider disablement reduces capacity if classification is wrong] -> Exclude model-missing and partial-output failures from provider trip evidence and preserve operator override controls.

## Migration Plan

1. Add the new requirement deltas for `model-router-service`.
2. Refactor router state so model exhaustion cooldowns and provider-breaker state are stored separately.
3. Update provider adapters to classify exhaustion signals precisely enough for the new state machine.
4. Update routing flow so retries re-enter ranked candidate selection while honoring active cooldowns and provider disablement.
5. Extend debug and metrics surfaces to expose the new state.
6. Add unit and integration tests for model-ladder escalation, provider tripping, cross-provider retries, and probe recovery.

Rollback is straightforward: revert to the previous router failure-handling path and existing cooldown semantics if the new breaker proves too aggressive in live validation.

## Open Questions

- Whether provider probe failures should escalate from `6h` to `12h` and `24h`, or use a configurable cap from the first implementation.
- Whether explicit OpenRouter response-body parsing should distinguish quota exhaustion from transient peak-capacity throttling beyond the existing `429` classification.
