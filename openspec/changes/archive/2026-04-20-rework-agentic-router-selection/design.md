## Context

`ghostship-hermes-router` currently combines three broad ideas that no longer match the desired operating model:

1. it keeps multiple logical aliases (`auxiliary`, `coding`, `agentic`, `vision`, `tts`) even though the repo now only cares about one normal execution lane;
2. it treats NVIDIA Build as a tiny repo-curated allowlist instead of discovering the real free catalog; and
3. it interleaves providers too early, so normal retryable model failures can move traffic away from the preferred provider before there is strong evidence that the provider's free tier is actually exhausted.

The desired replacement is narrower and more opinionated:

- the router should expose one normal alias: `agentic`;
- model ordering should come entirely from a repo-owned usable-model ranking supplied for the currently known free inventories;
- newly discovered models should not be routed until they are manually categorized by policy;
- providers should be sticky in strict order `nvidia-build` then `opencode-zen` then `openrouter`;
- switching providers should be exceptional and tied to clear free-tier exhaustion or the absence of eligible discovered models, not ordinary retryable model noise;
- the router should infer probable daily free-tier exhaustion even when providers expose only indirect evidence such as repeated pacing, generic quota failures, or zero-output exhaustion.

This is a cross-cutting router contract change because it touches provider discovery, ranking state, failover semantics, managed Hermes config, Discord forced-channel wiring, debug surfaces, and validation.

## Goals / Non-Goals

**Goals:**

- Make `agentic` the only repo-supported router alias for normal model routing.
- Replace NVIDIA allowlist-only inventory with live catalog discovery while retaining free-only filtering and explicit allow/block controls.
- Let the user supply explicit per-provider usable rankings and explicit per-provider unused-model lists.
- Keep newly discovered models out of routing until they are manually categorized into one of those policy buckets.
- Keep a top-five ranked usable reserve per provider and limit normal routing to the best three currently eligible models from that set.
- Keep routing sticky to `nvidia-build`, then `opencode-zen`, then `openrouter` until the active provider is clearly exhausted for free usage.
- Infer likely daily free-tier exhaustion from provider behavior and avoid reusing a provider too aggressively until a plausible reset window or recovery probe succeeds.
- Preserve intra-provider retries across lower-ranked models so transient model failures do not cause provider churn.
- Keep sessions sticky to the chosen provider and preferably the chosen model unless a failure or policy event requires movement.
- Expose operator-facing inventory surfaces that list uncategorized discovered models and explicitly unused discovered models so ranking maintenance is visible and manual.
- Store the router's usable rankings, unused-model lists, provider rules, and recovery thresholds in a single repo-owned policy surface instead of scattering them across unrelated env vars.
- Update managed runtime and Discord pinned-channel config so `ghostship-router` means `agentic`, not `coding`.
- Seed the initial per-provider top-five usable ranking from the supplied Hermes-weighted ranking.

**Non-Goals:**

- Reworking the direct Codex primary lane or the non-router primary/fallback model contract outside the managed custom-provider alias name.
- Designing a generic multi-alias strategy for `vision`, `tts`, `auxiliary`, or `coding`.
- Automating the initial usable list or unused list from model scores alone without a maintained repo-owned policy file.
- Replacing provider health, metrics, or cooldown machinery wholesale when targeted semantic changes are sufficient.
- Building a full learned router, adaptive quality classifier, or external evaluation service before the simpler repo-owned policy design is validated.

## Decisions

### 1. Collapse normal router selection to a single logical alias

The router will keep one normal routing alias: `agentic`.

Why:

- It matches the actual usage target.
- It removes alias-local ranking divergence that currently lets the same model score differently across buckets the repo does not intend to use.
- It simplifies validation, observability, and managed runtime wiring.

Alternative considered:

- Keep the other aliases but simply stop using them in managed config. Rejected because dead aliases still shape ranking code, discovery policy, tests, docs, and operator expectations.

### 2. Replace NVIDIA curated inventory with discovered free catalog plus repo policy overlays

NVIDIA Build inventory will be fetched from the provider catalog instead of a hardcoded tuple. After discovery, the router will apply:

- free-endpoint filtering;
- repo-owned usable and unused policy overlays;
- normal capability and modality filtering for the `agentic` lane.

Why:

- The current three-model NVIDIA inventory is artificially smaller than the actual public free pool.
- The user wants ranking policy, not discovery suppression, to decide which discovered models matter.

Alternative considered:

- Keep curated defaults and only allow opt-in extra models through env. Rejected because it preserves the core inventory bottleneck and shifts too much policy maintenance into one-off config.

### 3. Use explicit usable rankings and explicit unused-model lists as the primary selection source

The router will consume repo-owned per-provider usable rankings of known-good agentic models and repo-owned per-provider unused-model lists for discovered models that should never be tried. Only explicitly ranked usable models are eligible for normal routing. Newly discovered models that are not in either policy bucket remain uncategorized and are not routed.

Why:

- The user wants explicit control over the current model pool.
- It makes ranking auditable and stable across refreshes.
- It avoids pretending that lightweight inference can capture current model quality.

Alternative considered:

- Continue heuristic-first ranking and use manual weights only as minor nudges. Rejected because it does not give enough control over obviously weak models such as the user-called-out Trinity lane.

### 4. Keep uncategorized models visible but unroutable

Newly discovered models that are not explicitly present in the usable rankings or the unused-model lists remain uncategorized. Uncategorized models are visible through a dedicated inventory surface, but they never become normal routing candidates until the policy file is updated.

Why:

- Discovery should not require a source edit every time a provider adds a model.
- Unknown models should not silently enter routing.
- The operator needs a clean queue of new models to review.

Alternative considered:

- Admit uncategorized models through heuristics. Rejected because the user wants manual control over what Hermes is allowed to use.

### 5. Keep a top-five reserve per provider and route across the best available three

Each provider will keep a ranked top-five usable set in policy. For any given request, the normal routing candidate set is the highest-ranked three models from that top-five set that are currently eligible after cooldown, temporary unavailability, and provider-health filtering.

Why:

- The user wants the live failover lane to stay small and curated.
- A five-model reserve prevents one dead slot from collapsing the active candidate set too aggressively.
- Three active models per provider still preserves local retries without letting the long tail pollute routing.

Alternative considered:

- Route across every ranked usable model. Rejected because most long-tail models are not worth spending retries on.

### 5.1 Seed the initial top-five usable set from the supplied ranking

The initial usable ranking seed for implementation is:

- `nvidia-build`
  - `minimaxai/minimax-m2.7`
  - `qwen/qwen3-coder-480b-a35b-instruct`
  - `moonshotai/kimi-k2-thinking`
  - `deepseek-ai/deepseek-v3.2`
  - `z-ai/glm-4.7`
- `opencode-zen`
  - `big-pickle`
  - `minimax-m2.5-free`
  - `trinity-large-preview-free`
  - `nemotron-3-super-free`
  - `gpt-5-nano`
- `openrouter`
  - `qwen/qwen3-next-80b-a3b-instruct:free`
  - `google/gemma-4-31b-it:free`
  - `google/gemma-4-26b-a4b-it:free`
  - `openai/gpt-oss-120b:free`
  - `meta-llama/llama-3.3-70b-instruct:free`

These are the only initial ranked usable models required for normal routing. For each provider, the router picks the best three currently eligible models from this five-model set. All other discovered models start either uncategorized or explicitly unused once the operator supplies those lists.

Why:

- The user has already supplied a concrete Hermes-weighted ranking.
- Free-only agentic routing should start from explicit, narrow choices rather than another round of scoring debate.
- A five-model reserve preserves operator intent when one of the top three is temporarily unavailable.

### 6. Make provider order strict and sticky

Candidate selection will become two-stage:

1. choose the highest-priority provider with eligible agentic candidates: `nvidia-build`, then `opencode-zen`, then `openrouter`;
2. rank only that provider's candidates and retry within that provider first.

Cross-provider movement happens only when the active provider has become unavailable for free-tier reasons or has no eligible discovered models left.

Why:

- This matches the user's explicit desired provider policy.
- It prevents one noisy model from immediately pushing traffic into a less preferred provider.

Alternative considered:

- Keep current cross-provider interleaving with stronger provider weights. Rejected because weighting still allows eager provider switching in edge cases the user wants to suppress.

### 7. Treat free-tier exhaustion as the primary provider-failover signal

The router will distinguish between:

- model-local retryable failures: stay within the same provider and try the next ranked model there;
- provider exhaustion signals: provider pacing, quota exhaustion, insufficient balance, repeated zero-output exhaustion, or other explicit free-tier exhaustion evidence;
- provider inventory absence: no eligible discovered free agentic models remain.

Only the second and third classes will allow normal cross-provider failover.

Why:

- The user wants provider failover to mean “we ran out of free usage here,” not “one model timed out once.”

Alternative considered:

- Fail over providers on any retryable provider-wide degradation. Rejected because it preserves the churn the user wants to remove.

### 8. Add provider-aware daily-limit inference instead of relying on one explicit quota error

The router will maintain a provider-level exhaustion classifier that can promote a provider from "suspect" to "probably daily-limit exhausted" based on accumulated evidence such as:

- explicit quota or insufficient-balance responses;
- provider pacing or retry-after responses that repeat across multiple requests or distinct models;
- repeated zero-output exhaustion-class failures from distinct models on the same provider inside a bounded window;
- provider-specific heuristics for known free-tier behavior, including a configurable daily-reset assumption when upstream does not expose one directly.

Once the classifier decides a provider is probably daily-limit exhausted, the router will suppress that provider for normal routing until one of these happens:

- the configured daily-reset window has passed;
- a background or on-demand recovery probe succeeds;
- an operator override clears the exhausted state.

Why:

- Free providers often do not tell you cleanly that the daily pool is gone.
- Waiting for one literal quota string is too brittle.
- Repeatedly hammering an exhausted provider wastes latency and works against the desired provider order.

Alternative considered:

- Only trust explicit provider quota errors. Rejected because some providers surface daily exhaustion as vague pacing or generic failures.

### 9. Expose inventory maintenance endpoints for uncategorized and unused models

The router will expose at least two operator-facing inventory surfaces:

- one endpoint or debug surface listing uncategorized discovered models that are not present in the policy;
- one endpoint or debug surface listing discovered models that were explicitly marked unused by policy and therefore never enter routing.

Why:

- The operator wants manual review of catalog churn.
- It keeps the routing set hard and predictable while still making discovery useful.

Alternative considered:

- Force operators to infer these lists indirectly from raw provider inventory dumps. Rejected because that makes policy maintenance slower and noisier.

### 10. Add session stickiness without adaptive reranking

The router will prefer staying on the same provider and, when reasonable, the same model for a continuing session, but it will not do adaptive request-shape reranking inside a provider. Ranked policy order stays authoritative.

Why:

- It reduces cross-turn behavior jitter.
- It preserves deterministic policy behavior.

Alternative considered:

- Add adaptive request-shape reranking. Rejected because the user wants a hard manually curated order.

### 11. Keep observability aligned with the new routing semantics

Debug and metrics surfaces must show:

- the chosen provider order;
- whether a request stayed inside one provider or crossed to another;
- the exact evidence that caused provider failover;
- whether the provider is in a short cooldown or considered probably daily-limit exhausted;
- whether a model came from the explicit usable ranking, the explicit unused list, or the uncategorized discovered set;
- whether session stickiness affected the final choice.

Why:

- Without this, provider stickiness and exhaustion-only failover will be hard to validate or tune.

### 12. Consolidate policy into one repo-owned configuration surface

The router will keep usable rankings, unused-model lists, provider-specific exhaustion adapters, and recovery thresholds in one repo-owned policy surface. Env vars may still override selected values, but the primary contract should be one coherent policy artifact.

Why:

- The router is becoming policy-heavy.
- Spreading this logic across many unrelated env vars will make tuning brittle and opaque.

Alternative considered:

- Keep adding more env vars. Rejected because it becomes hard to reason about the effective policy.

### 13. Update runtime and Discord wiring to `agentic`

The managed Hermes `ghostship-router` custom-provider model and the Discord forced-response route will move from `coding` to `agentic`.

Why:

- Leaving `coding` in managed wiring after collapsing the router to `agentic` would make the managed contract internally inconsistent.

## Risks / Trade-offs

- [Risk] Static rankings can become stale as provider quality shifts. → Mitigation: keep uncategorized-model inventory visible and make policy updates easy and durable.
- [Risk] Exhaustion-only provider failover may reduce liveness during non-exhaustion provider incidents. → Mitigation: keep strong intra-provider retries and make the exact provider-abandon criteria configurable and observable.
- [Risk] Daily-limit inference can misclassify transient throttling as full-day exhaustion. → Mitigation: require multiple corroborating signals, distinguish short cooldown from probable daily exhaustion, and re-admit providers through timed recovery probes.
- [Risk] Session stickiness can hold a session on a mediocre model too long. → Mitigation: let hard failures and explicit policy rank breaks override stickiness.
- [Risk] NVIDIA catalog discovery may surface many irrelevant free endpoints such as embeddings, guardrails, or media tools. → Mitigation: apply free-only filtering plus strict `agentic` capability gating before ranking, and support durable explicit usable/unused policy.
- [Risk] Removing extra aliases is a breaking API change for any consumer expecting `coding`, `auxiliary`, `vision`, or `tts`. → Mitigation: update managed runtime, Discord routing, docs, and validation together in one change.
- [Risk] Leaving uncategorized models unroutable can make the router miss a newly good model until manual review. → Mitigation: expose uncategorized inventory directly and keep policy maintenance explicit.

## Migration Plan

1. Introduce one repo-owned router policy surface for the initial per-provider usable rankings, explicit unused-model lists, provider rules, and recovery thresholds.
2. Implement NVIDIA catalog discovery with free-endpoint filtering and `agentic` eligibility filtering.
3. Collapse normal alias exposure and candidate selection to `agentic`.
4. Add uncategorized and unused-model inventory surfaces so discovery remains visible without entering routing.
5. Switch provider selection from cross-provider shortlist interleaving to strict provider stickiness with exhaustion-gated failover and daily-limit inference.
6. Update managed Hermes config and Discord pinned routing from `coding` to `agentic`.
7. Update tests, validation, docs, and debug surfaces to the new contract.
8. Roll back, if needed, by restoring the old alias set, curated NVIDIA inventory, and current cross-provider interleaving policy from the previous image revision.

## Open Questions

- What exact model ids belong in the initial explicit unused lists for each provider?
- Should provider-auth or provider-refresh failures hard-fail the request instead of falling through to a lower-priority provider, or should they remain a separate emergency failover class?
- Should deprecated NVIDIA free endpoints be discoverable but excluded by default, or omitted at discovery time entirely?
- What daily-reset assumptions should the router use per provider when the upstream service does not expose an explicit reset timestamp?
