## Context

`ghostship-router` currently builds providers only for OpenRouter and OpenCode Zen, then ranks free-eligible models across aliases using a mix of family priors, rolling health, persisted ranking output, and provider-specific cooldown state. The candidate-selection path already slices each provider lane during discovered routing, but that behavior is implicit, limited to one path, and not yet part of the router contract.

The requested change adds NVIDIA Build API as a first-class provider, but the goal is not broad catalog ingestion. The user wants a curated free-only NVIDIA lane that receives higher routing priority and only scores the top three NVIDIA coding models. The user also wants the managed Discord router channel to use alias `coding` instead of `agentic`, while keeping the broader runtime fallback behavior unchanged unless a later change explicitly revisits it.

## Goals / Non-Goals

**Goals:**
- Add a native `nvidia-build` provider to the router.
- Keep NVIDIA routing restricted to a repo-curated free-only inventory.
- Make per-bucket routing retain at most the top 3 scored models per provider before global interleaving and failover.
- Ensure provider priority is explicit and favors NVIDIA when healthy free candidates are otherwise comparable.
- Change the managed Discord free-response router-channel pin from `agentic` to `coding`.
- Keep docs, tests, and OpenSpec contracts aligned with the new provider and channel behavior.

**Non-Goals:**
- Changing the direct primary runtime lane away from `opencode-go/minimax-m2.7`.
- Replacing the existing deterministic scoring model.
- Expanding the router to broad NVIDIA catalog discovery across all Build API models.
- Making paid NVIDIA models routable.
- Changing the Codex-pinned Discord channel behavior.

## Decisions

### Add NVIDIA as a native OpenAI-compatible chat provider with curated inventory
The router will add a dedicated `nvidia-build` provider that uses the NVIDIA hosted OpenAI-compatible chat-completions surface. Inventory for this provider will come from a repo-curated list of model ids instead of dynamic provider-side discovery. The curated inventory will be treated as free-only router candidates and will be filtered to models that satisfy the alias capability rules just like the other providers.

This avoids depending on unstable or incomplete public catalog enumeration semantics while matching the user’s intent: only a small curated NVIDIA subset should participate in routing.

Alternative considered: dynamic discovery from the full NVIDIA catalog. Rejected because the user explicitly wants only the top three NVIDIA models scored, and the router should not absorb a large unstable model surface just to discard most of it later.

### Make per-provider per-bucket shortlist capping an explicit routing rule
For each logical bucket (`auxiliary`, `coding`, `agentic`, `vision`, `tts`), the router will score all eligible models for each enabled provider, keep only that provider’s top 3 scored models for the bucket, and only then interleave providers into the final alias candidate list.

This turns the current implicit lane slicing into an explicit contract and keeps inventory growth from one provider from overwhelming the routing pool. The same shortlist cap should apply consistently to discovered routing and any provider-aware reranking inputs that depend on alias candidate sets.

Alternative considered: cap only the final merged alias list. Rejected because it lets one large provider dominate scoring work and failover ordering before the merge.

### Replace ad hoc provider bias with explicit provider-priority policy
Provider priority will be expressed through explicit router policy rather than a hardcoded OpenRouter bump. NVIDIA will receive the highest default provider priority, while OpenCode Zen and OpenRouter remain below it. Provider priority will still be subordinate to free-only eligibility, alias capability fit, active cooldowns, pacing, and recent health.

This makes the “prefer NVIDIA” requirement auditable and adjustable without leaving legacy bias toward OpenRouter in place.

Alternative considered: stack NVIDIA-specific model weights on top of the existing OpenRouter bias. Rejected because it obscures routing intent and leaves contradictory provider favoritism in the scorer.

### Keep NVIDIA’s initial scope coding-first
The initial curated NVIDIA inventory will target the `coding` lane first, using three repo-approved free model ids that are known to fit the router’s current family priors. Other aliases may still classify those models if capability metadata permits, but the curated provider inventory itself will be chosen around coding usefulness rather than trying to populate all buckets on day one.

This matches the user’s explicit preference for “the best free models” in the router channel and avoids overfitting vision or tts behavior before there is evidence that NVIDIA should supply those lanes.

Alternative considered: force NVIDIA models into every bucket. Rejected because it would create low-signal candidates in buckets where the curated models do not clearly belong.

### Change the Discord router channel pin and default custom-provider model to `coding`
The managed Discord forced router channel will change its forced alias from `agentic` to `coding`. The repo-owned `ghostship-router` custom provider default model should change to `coding` as well so the managed home seed, advisory UX, and forced-channel route all describe the same router lane.

This keeps the runtime consistent: the route a user is told about, the route the channel actually uses, and the route shown in managed defaults should all match.

Alternative considered: change only the forced Discord patch and leave the custom provider default as `agentic`. Rejected because it preserves confusing drift between runtime behavior and visible configuration defaults.

## Risks / Trade-offs

- [Curated NVIDIA model ids can go stale] → Keep the curated list repo-owned and test inventory refresh and missing-model handling against the provider adapter.
- [Higher NVIDIA priority could suppress better-performing non-NVIDIA models] → Keep provider priority below health, cooldown, and capability gating, and expose the resulting score breakdown in existing debug surfaces.
- [Per-provider top-3 capping can hide a useful fourth model] → Preserve override and alias-pin mechanisms so operators can still force a model into routing when needed.
- [Changing the Discord router channel alias could surprise existing sessions] → Update the forced-channel message, specs, and validation together so the new lane is explicit and tested.

## Migration Plan

1. Extend router config and provider construction to support `NVIDIA_BUILD_API_KEY` and the native `nvidia-build` provider.
2. Add the curated NVIDIA model inventory and integrate it into routing, refresh, and observability.
3. Make per-provider top-3-per-bucket capping explicit and consistent in candidate selection.
4. Replace legacy provider bias with explicit provider priority that favors NVIDIA.
5. Change the managed Discord router-channel pin and `ghostship-router` default model from `agentic` to `coding`.
6. Update router docs, runtime docs, and smoke coverage to reflect the new provider and channel contract.

Rollback is straightforward: remove the NVIDIA provider wiring, restore the previous provider-priority defaults, and set the Discord router channel back to `agentic`.

## Open Questions

- Which exact three NVIDIA model ids should be the initial curated coding set if the hosted catalog changes before implementation?
- Should NVIDIA participate in auxiliary ranking-worker selection immediately, or remain request-routing-only in the first pass?
- Whether the per-provider top-3 rule should remain fixed or later become a dedicated config knob separate from the existing lane-limit setting.
