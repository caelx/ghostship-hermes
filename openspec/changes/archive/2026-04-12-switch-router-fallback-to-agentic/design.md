## Context

The repo already has an in-flight source change that flips the managed runtime to direct `opencode-go/minimax-m2.7` primary, but that change currently points the router fallback at alias `coding`. After validating the live router alias inventory, the intended fallback lane is `agentic`, not `coding`. The same source change also sets `GHOSTSHIP_ROUTER_DISABLED_MODELS=openrouter/free` by default for the managed image, and that contract needs to be carried through validation and docs.

The more important failure mode is that source changes have not always been reflected in the published image. This change therefore needs to prove the contract at the published-image and deployed-host layers rather than stopping at source edits. The live host also still demonstrates the old gateway pidfile regression: `hermes doctor` removes `/home/hermes/.hermes/gateway.pid` even though the managed gateway service remains running. The source-side pidfile matcher fix already landed separately, so this proposal treats live verification of that behavior as part of the rollout gate.

One important deployment constraint remains: the live `opencode-go` path currently reports `HTTP 404`, so rollout should validate the direct MiniMax path before treating the new primary lane as healthy.

## Goals / Non-Goals

**Goals:**
- Keep `opencode-go/minimax-m2.7` as the managed primary model path.
- Change the managed router fallback alias from `coding` to `agentic`.
- Keep `openrouter/free` blocked by default through the managed router env contract.
- Update automated validation and operator docs so they assert the final intended contract.
- Require published-image and live-host verification for both the model contract and the managed gateway pidfile behavior.

**Non-Goals:**
- Redesign router alias semantics or ranking behavior beyond the exact default blocked model.
- Replace the local router fallback with a different provider or endpoint.
- Re-implement the gateway pidfile matcher logic in this change; that source fix already exists and needs rollout proof.
- Solve the live `OpenCode Go (HTTP 404)` provider issue in the same change.

## Decisions

### 1. Keep the direct MiniMax primary lane and retarget the router fallback alias to `agentic`
The managed config should continue using `model.provider = opencode-go` and `model.default = minimax-m2.7`, while `fallback_model` should point at router alias `agentic`.

Rationale:
- That preserves the requested “OpenCode Go primary, router fallback” order.
- `agentic` is the actual alias name exposed by the router contract and better matches the desired stronger fallback lane.
- The source diff stays narrow and avoids reworking the primary model flip again.

Alternative considered: revert to router-primary and use `agentic` as the main lane. Rejected because it changes the requested runtime order.

### 2. Keep `openrouter/free` blocked through the managed router env default
The exact backend id `openrouter/free` should remain excluded by setting `GHOSTSHIP_ROUTER_DISABLED_MODELS=openrouter/free` in the managed router service environment.

Rationale:
- The router already supports exact model blocking through config; no router-service code change is required.
- This keeps the exclusion image-scoped and reversible.
- It avoids changing the broader free-model selection rules for other providers or OpenRouter models.

Alternative considered: hardcode a router-service special case for `openrouter/free`. Rejected because the existing env/config contract already solves the problem more cleanly.

### 3. Validate the final runtime contract at source, published-image, and live-host layers
Validation should assert the managed config values, the managed router env default, and the deployed runtime state directly.

Rationale:
- The previous failure was not only the wrong fallback lane; it was also that a pushed source change did not prove up in the published image.
- Smoke coverage is the cheapest place to catch a wrong alias or missing env default before publish.
- Live checks must confirm the deployed host actually received the fixed config.

Alternative considered: document the new contract without changing tests or rollout checks. Rejected because that would allow the same drift to recur.

### 4. Treat gateway pidfile survival after `hermes doctor` as a rollout gate
The rollout is not complete unless `/home/hermes/.hermes/gateway.pid` still exists after running `hermes doctor` against the deployed image.

Rationale:
- The live host still shows the old regression even though the source-side fix has already landed.
- Dashboard and Hermes health surfaces both depend on `gateway.pid` as the primary liveness marker.
- This is the simplest end-to-end proof that the correct image actually shipped.

Alternative considered: leave pidfile verification to the separate archived change. Rejected because the live defect is still present and should be gated in the same publish/revalidate sequence.

## Risks / Trade-offs

- [Live `opencode-go` remains unhealthy] -> Gate rollout validation on confirming the direct MiniMax path works, and do not treat the deploy as healthy if `OpenCode Go (HTTP 404)` persists.
- [Fallback alias semantics drift again] -> Assert the exact `fallback_model.model = agentic` value in smoke coverage and docs.
- [`openrouter/free` block is lost during later env refactors] -> Assert `GHOSTSHIP_ROUTER_DISABLED_MODELS=openrouter/free` in image validation instead of relying on docs alone.
- [Published image still diverges from source] -> Require post-publish inspection of the built image and post-deploy inspection of the live host.
- [Gateway pidfile regression survives rollout] -> Run `hermes doctor` as part of live validation and fail the rollout if `gateway.pid` disappears.

## Migration Plan

1. Update the managed Hermes config so the primary lane stays `opencode-go/minimax-m2.7` and the router fallback alias becomes `agentic`.
2. Keep the managed router env default `GHOSTSHIP_ROUTER_DISABLED_MODELS=openrouter/free`.
3. Update dashboard fixtures, smoke validation, and docs to match the final contract.
4. Publish a new image and inspect it directly to confirm the managed config/default env contract is present.
5. Deploy the image to `chill-penguin-root2`.
6. Re-run live validation to confirm:
   - `/home/hermes/.hermes/config.yaml` shows direct MiniMax primary
   - `fallback_model.model` is `agentic`
   - the managed router environment includes `GHOSTSHIP_ROUTER_DISABLED_MODELS=openrouter/free`
   - `/home/hermes/.hermes/gateway.pid` survives `hermes doctor`
   - the direct `opencode-go` path is healthy enough for the new primary lane

Rollback is straightforward: restore the previous fallback alias in source, rebuild, and redeploy.

## Open Questions

- Should rollout of the new primary lane be blocked until the live `OpenCode Go (HTTP 404)` issue is fixed, or is a best-effort publish acceptable while fallback still exists?
