## Context

The current change tightened exhaustion failover, but live validation showed that the router still spends free-tier budget on startup ranking probes before any real traffic arrives. On `chill-penguin`, startup called provider inventory endpoints and then immediately made ranking-worker requests against free models, producing early Zen `429` responses before the first user request.

The same validation also showed that provider disablement is too aggressive for temporary throttles. OpenRouter returned a temporary upstream `429` naming the upstream provider, while OpenCode Zen returned `FreeUsageLimitError` with a `Retry-After` window of roughly 35 minutes. Those signals are different from explicit account exhaustion, and the router should not convert them into blanket six-hour provider disablement by default.

Finally, the runtime currently needs an explicit credential rule for Zen. The router must prefer `OPENCODE_GO_API_KEY` over `OPENCODE_API_KEY` when both are set.

## Goals / Non-Goals

**Goals:**

- Eliminate worker-assisted ranking calls during startup refresh.
- Keep routing available on cold start by using deterministic heuristic ordering plus any persisted ranking data that already exists.
- Make provider credential precedence explicit and testable.
- Make provider-wide disablement less aggressive for temporary upstream throttles while preserving transparent ranked failover.
- Preserve strong provider disablement for explicit balance or quota exhaustion and repeated failed recovery probes.

**Non-Goals:**

- Removing inventory refresh on startup.
- Replacing the existing deterministic scoring model with a new ranking algorithm.
- Surfacing provider credential source details to callers.
- Changing non-exhaustion failure handling outside the provider-suppression tuning required here.

## Decisions

### Do not run assisted ranking during startup

Startup refresh will load provider inventory and persisted state only. It will not invoke worker-assisted ranking during the initial `startup` refresh path.

Cold-start candidate ordering will use the existing deterministic score breakdown and any persisted ranking rows already stored in the state database. If assisted ranking remains enabled, it must run later through a deferred path such as a scheduled refresh after the service is already healthy, or another explicit operator-controlled trigger.

This avoids burning free-lane requests before the first user request while still preserving stable routing order.

### Keep deterministic ranking as the default readiness path

The router already has a deterministic scoring model based on alias fit, provider and model weights, recency, capability metadata, and persisted health. That deterministic score becomes the default startup ranking path.

Persisted ranking data may still influence scoring when available, but lack of fresh assisted ranking data must not block startup or trigger outbound worker calls.

### Make provider credential precedence explicit

Provider credential resolution will be:

- OpenRouter: `OPENROUTER_API_KEY`
- OpenCode Zen: prefer `OPENCODE_GO_API_KEY`, then fall back to `OPENCODE_API_KEY`

This precedence must be encoded in config loading and covered by tests so live runtime env files cannot silently select the wrong Zen credential when both names are present.

### Use provider-scoped pacing and `Retry-After` before provider disablement

Temporary upstream throttles should first update provider-scoped pacing state, not immediately disable the whole provider for six hours.

The router should maintain base provider spacing of `3 seconds` for OpenRouter and `2 seconds` for OpenCode Zen between requests to the same provider. Temporary throttle responses should raise those spacing windows through a short provider backoff ladder before any hard provider disablement is considered.

The router should treat these as temporary throttle signals:

- OpenRouter `429` responses that explicitly describe temporary upstream rate limiting
- OpenCode Zen `FreeUsageLimitError` responses with `Retry-After`

When those responses provide `Retry-After`, the router should apply that value as the cooldown input for the affected provider lane, and only escalate to provider-wide suppression if later evidence proves the whole provider is broadly unavailable.

### Reserve long provider disablement for stronger signals

Six-hour provider disablement remains valid for stronger signals such as:

- explicit `insufficient_balance`
- explicit quota exhaustion without a shorter retry window
- repeated failed probe recovery after an earlier provider-wide disablement
- stronger same-provider exhaustion evidence that persists beyond a temporary throttle window

Temporary free-lane `429` bursts on two models in one request are not enough by themselves when the provider response clearly says to retry shortly.

### Rank top-three provider lanes and alternate between providers

For each alias, the router should rank the top three eligible models for OpenRouter and the top three eligible models for OpenCode Zen separately. Request-time failover should then alternate between provider lanes instead of exhausting multiple models from the same provider in a row.

This makes the retry path explicitly provider-aware, reduces burst pressure on a single provider, and still respects ranked ordering within each provider lane.

### Keep observability explicit about suppression source and provider pacing

Debug and metrics surfaces should distinguish:

- provider pacing delay due to temporary throttle
- model cooldown due to model-specific failures
- provider suppression due to explicit exhaustion
- provider suppression due to failed probe recovery
- startup readiness without assisted ranking

Operators need to see why a provider or model is unavailable before deciding whether to wait, override, or change credentials.

## Risks / Trade-offs

- [Heuristic-only startup order may be weaker than fresh assisted ranking] -> Persist prior ranking outputs when available and keep deferred assisted ranking optional for later refinement.
- [Temporary throttle detection may under-disable a truly unhealthy provider] -> Keep provider-wide suppression for explicit exhaustion and probe failures, and continue tracking provider evidence across requests.
- [Credential precedence changes may alter current Zen traffic unexpectedly] -> Make the precedence explicit in config tests and document it in the spec delta.
- [Deferred assisted ranking could still burn quota if left fully automatic later] -> Require the startup path to skip assisted ranking entirely and make any later ranking trigger explicit in the implementation tasks.

## Migration Plan

1. Update the `model-router-service` change artifacts so startup ranking, credential precedence, and softer provider suppression are required behavior.
2. Change router startup refresh so it does not invoke assisted ranking.
3. Update credential resolution to prefer `OPENCODE_GO_API_KEY` for Zen.
4. Update provider error normalization and cooldown handling to use `Retry-After` and classify temporary throttles separately from hard exhaustion.
5. Retune provider suppression so six-hour disablement is reserved for strong exhaustion evidence.
6. Extend tests for startup behavior, env precedence, and softened provider suppression.

Rollback is straightforward: restore startup assisted ranking and the prior suppression thresholds if live routing quality regresses more than the saved startup capacity is worth.

## Open Questions

- Whether deferred assisted ranking should remain scheduled by default after startup or become opt-in only.
- Whether Zen `FreeUsageLimitError` should apply provider-wide cooldown for the exact `Retry-After` window or remain model-scoped until repeated evidence proves provider-wide exhaustion.
