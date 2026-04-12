## Context

Recent live validation on `chill-penguin-root2` showed that the image is closer to healthy than earlier broken publishes, but it still does not satisfy the full runtime contract. The managed model order on the deployed host is still wrong relative to the intended source direction, the router default disabled-model setting is not proven live, the dashboard does not expose the full managed agent config needed to validate that contract, and the dashboard terminal flow has only been validated at the API/proxy level instead of through the browser UI that operators actually use.

Separately, the managed gateway pidfile regression is still operationally important: `hermes doctor` can remove `/home/hermes/.hermes/gateway.pid` even while the managed gateway service is running. The source-side matcher fix has already been authored, but the live image must prove it. Finally, prior pushes have shown that a source change is not enough; the published image and deployed host both need explicit inspection.

The live `opencode-go` path has also reported `HTTP 404`, which is a deployment blocker if direct `opencode-go/minimax-m2.7` is the shipped primary lane. Cold-start health still has an avoidable early-probe race as well. This proposal therefore combines source-contract fixes with publish and live-proof requirements.

## Goals / Non-Goals

**Goals:**
- Ship direct `opencode-go/minimax-m2.7` as the managed primary model path.
- Ship router alias `agentic` as the managed fallback path via `http://127.0.0.1:8788/v1` using `OPENAI_API_KEY`.
- Keep `GHOSTSHIP_ROUTER_DISABLED_MODELS=openrouter/free` as the default router exclusion.
- Make the dashboard expose the actual managed agent config, including enough information to validate primary and fallback model wiring.
- Validate browser-driven ttyd terminal opening end to end.
- Require post-publish and post-deploy inspection of the image contract.
- Verify `/home/hermes/.hermes/gateway.pid` remains present after `hermes doctor`.
- Remove avoidable cold-start health probe failures and refuse to call the image healthy if the direct primary lane is broken.

**Non-Goals:**
- Introduce interactive auth flows or preseed credentials.
- Redesign router ranking beyond the exact `openrouter/free` exclusion.
- Rework the single-agent topology or persisted home layout.
- Add new dashboard features unrelated to runtime validation.

## Decisions

### 1. Treat the intended runtime contract as direct MiniMax primary with router `agentic` fallback
The managed config should set `model.provider = opencode-go`, `model.default = minimax-m2.7`, and `fallback_model` should point at router alias `agentic` through the local OpenAI-compatible endpoint.

Rationale:
- That is the requested runtime order.
- `agentic` is the correct router alias name for the stronger fallback lane.
- It avoids continuing the old router-primary `coding` default after the requested contract changed.

### 2. Keep `openrouter/free` blocked through managed router env
The managed router service should keep `GHOSTSHIP_ROUTER_DISABLED_MODELS=openrouter/free` by default.

Rationale:
- The router already supports exact backend-id exclusions.
- This is a runtime contract issue, not a router ranking redesign.

### 3. Make the dashboard report the actual agent config contract
The dashboard status payload and UI should expose enough managed config data to validate both the primary and fallback model contract, not just the primary `model.default` and `base_url`.

Rationale:
- The current status reader only parses the top-level `model` block, so the UI cannot prove fallback wiring.
- Operators are using the dashboard as the live validation surface.

### 4. Validate terminal opening at the browser surface
The repo should add an end-to-end dashboard validation path that opens a terminal through the actual browser UI and proves the embedded ttyd session becomes usable.

Rationale:
- Current smoke coverage validates `/api/terminal/open` and proxy reachability, but that does not prove the browser workflow works.
- The live report was specifically about the dashboard not opening the ttyd terminal.

### 5. Treat published-image and live-host inspection as part of the fix
The change is not complete when source is updated; it is complete only when the published image and deployed host are shown to contain the intended config, dashboard behavior, and pidfile behavior.

Rationale:
- This repo has already shipped source changes that did not materialize in the published image.
- The failure mode is at the artifact boundary, not only in source code.

### 6. Keep `gateway.pid` as the authoritative managed liveness marker and prove it survives `hermes doctor`
The rollout must confirm that the running managed gateway keeps `/home/hermes/.hermes/gateway.pid` even after `hermes doctor` runs.

Rationale:
- Dashboard status and Hermes readiness surfaces key off `gateway.pid`.
- The source-side matcher fix is not enough unless the published image proves it.

### 7. Gate rollout on primary-lane and cold-start health
If direct `opencode-go` still returns `HTTP 404`, the rollout should not be treated as healthy. The healthcheck should also stop failing for avoidable boot-time command-path races.

Rationale:
- A broken shipped primary lane invalidates the contract.
- An avoidable first-probe failure makes health noisy and harder to trust.

## Risks / Trade-offs

- [Direct `opencode-go` still fails live] -> Treat that as a rollout blocker, not an acceptable warning.
- [Dashboard status payload changes could break tests/UI assumptions] -> Update fixtures and browser validation together with the API shape.
- [Published image still drifts from source] -> Require explicit inspection of the published artifact and deployed host.
- [Gateway pidfile fix still fails to ship] -> Run `hermes doctor` during live validation and fail if `gateway.pid` disappears.
- [Browser terminal validation becomes flaky] -> Keep it focused on terminal-open and frame-availability rather than long interactive flows.

## Migration Plan

1. Update the managed runtime config to direct MiniMax primary plus router `agentic` fallback.
2. Keep the router disabled-model default for `openrouter/free`.
3. Extend dashboard status/UI to show the managed agent config contract and liveness markers.
4. Add browser-level terminal-open validation and config-display assertions.
5. Tighten cold-start/primary-lane validation.
6. Publish a new image and inspect the built artifact directly.
7. Deploy to `chill-penguin-root2`.
8. Re-run live validation to confirm:
   - managed config shows direct MiniMax primary and router `agentic` fallback
   - managed router env disables `openrouter/free`
   - dashboard shows the intended primary/fallback contract
   - dashboard terminal open works end to end
   - `gateway.pid` survives `hermes doctor`
   - direct `opencode-go` is healthy enough for the primary lane
   - cold-start health reaches healthy without the avoidable early probe failure

Rollback is straightforward: revert the runtime/dashboard contract changes, rebuild, and redeploy.
