## Context

The repo already has a concrete pattern for small Python web services: the new dashboard package uses `FastAPI` for the API surface and `uvicorn` as the local server process. The router should follow that pattern so its packaging, local execution model, and future runtime integration feel native to this repo rather than introducing a second service stack.

The previous router effort survives only as planning material. This fresh change needs to turn that intent into an implementation plan that can land incrementally instead of attempting full free-model orchestration in a single pass. The user also wants the router isolated as a new package at `packages/hermes-router`, which makes it possible to build and test the service independently before wiring it into the Hermes image.

The repo's local validation setup already uses ignored `.envrc` files that are not copied into git worktrees by default. The current main worktree has provider credentials available through environment variables for OpenRouter and Opencode, so the router plan should assume environment-driven local testing rather than checked-in credential fixtures.

## Goals / Non-Goals

**Goals:**
- Build a new router package at `packages/hermes-router`.
- Use `FastAPI` and `uvicorn` for the local API service.
- Expose a stable local API with logical aliases such as `lightweight`, `coding`, and `heavyweight`.
- Deliver the router in stages, with a minimal usable service first and richer routing state later.
- Keep provider-specific logic behind adapter boundaries so the API and routing layers stay stable.
- Use existing local provider credentials from environment variables for development and validation without duplicating secrets into the repo.
- Refresh and score candidate models from both OpenRouter and OpenCode Zen.
- Support Zen's mixed upstream endpoint families without exposing those differences to router callers.
- Keep failover, health, and timing data attached to concrete backend models rather than alias-level aggregates.
- Preserve a path to later integrate the router into the Hermes image and service supervision model.

**Non-Goals:**
- Making the router the default Hermes model endpoint in the first implementation stage.
- Building a browser UI or dashboard for router administration.
- Supporting every possible provider in v1.
- Solving advanced model classification with heavyweight online inference in the request path.
- Coupling phase 1 delivery to image-level systemd wiring if the standalone package is not ready.

## Decisions

### Create a new standalone package at `packages/hermes-router`
The router will live in its own package with repo-standard packaging metadata, tests, and `package.nix` wiring. This keeps the service separate from the Hermes image runtime glue and lets the package mature through direct local testing before image integration.

Alternative considered: embedding router code under `packages/hermes-image/`. Rejected because it would mix application code with image/runtime glue and make isolated testing harder.

### Use `FastAPI` for the API layer and `uvicorn` as the service entrypoint
The router will follow the dashboard package pattern: a `FastAPI` application object, a small `main()` entrypoint, and `uvicorn` for serving localhost traffic. This keeps the service stack aligned with existing repo patterns and gives the router a straightforward async HTTP surface for upstream provider calls and future readiness/debug endpoints.

Alternative considered: a custom HTTP server or Flask-style stack. Rejected because the repo already has a working `FastAPI` precedent and the router benefits from modern request validation and async support.

### Expose an OpenAI-compatible subset on localhost
The initial API surface should include `GET /v1/models`, `POST /v1/chat/completions`, `GET /healthz`, and `GET /readyz`. Callers should see stable logical model aliases, while the router resolves those aliases internally to provider/model candidates.

Alternative considered: inventing a router-specific API. Rejected because Hermes and related tools can adopt an OpenAI-style surface with less custom integration work.

### Stage delivery from static/minimal routing toward dynamic routing
Implementation will land in phases:

1. Package scaffold, config loading, stable aliases, health endpoints, and a minimal routing path.
2. Provider adapters, free-first candidate selection, retry/failover, and OpenCode Zen inventory support.
3. SQLite-backed state, startup/background inventory refresh, cooldown tracking, and richer observability.
4. Repo/runtime integration, image wiring, and operational documentation.

This sequencing keeps the first merge small enough to verify while preserving the long-term architecture from the original router concept.

Alternative considered: implementing discovery, persistence, failover, and image integration in one change. Rejected because it raises coordination and debugging risk before the public API contract is stable.

### Load provider credentials from environment and validate with existing local `.envrc` inputs
The router should read provider credentials from environment variables so local validation can reuse the repo's existing `.envrc`-managed inputs. The implementation plan should explicitly support `OPENROUTER_API_KEY` and `OPENCODE_API_KEY` when present, while keeping secrets out of committed config.

Alternative considered: checked-in local config fixtures with embedded test credentials. Rejected because it would push secret handling into source control and diverge from how this repo already handles local service validation.

### Use a free model for optional model-assisted bucketing and ranking
If the router adds background model-assisted classification or ranking, that maintenance workflow should use a configured free model.

Alternative considered: using a paid model for background bucketing or ranking. Rejected because it spends paid capacity on maintenance work even though the router's policy is free-first where possible.

### Treat OpenCode Zen as a first-class provider with mixed endpoint-family support
OpenCode Zen will be implemented as a real provider adapter that refreshes the Zen model inventory and can invoke whichever upstream request family a given Zen model requires. The router should normalize those upstream differences back into the same local `chat/completions` response shape.

The adapter should support at least:

- OpenAI-style `/chat/completions`
- OpenAI `/responses`
- Anthropic `/messages`
- Google-style `/models/{model}:generateContent` requests

Because the public Zen `GET /models` payload does not currently expose endpoint-family metadata, the adapter should keep a per-model endpoint-family cache and be able to probe alternate families when necessary.

Alternative considered: limiting the router to Zen models that already use `/chat/completions`. Rejected because it would exclude a large part of Zen's curated inventory and would not meet the stated requirement to support mixed endpoint families.

### Keep routing state and failover decisions at the concrete backend-model level
The routing engine should make candidate, cooldown, and failover decisions using concrete backend models, not alias-level aggregates. Alias names remain the caller-facing abstraction, but health and retry state are attached to the resolved provider and model pair.

Alternative considered: tracking health primarily at the alias level. Rejected because it hides which concrete backend is failing and makes cross-provider failover less reliable.

### Track best-effort time-to-first-text in addition to total latency
The router should retain overall request latency and, when the upstream protocol makes it feasible, best-effort latency to first returned text. This should be recorded in routing state and exposed through debug surfaces so operators can distinguish slow first-token behavior from slow total completion time.

Alternative considered: recording only total request duration. Rejected because it hides an important part of perceived responsiveness, especially when candidate selection spans different providers and endpoint families.

### Separate the API layer from adapters, routing, and state
The service should be structured as a small set of focused modules:

- `app.py` or equivalent API bootstrap
- request/response schemas
- config loading
- provider adapters
- routing engine
- inventory/state store
- background maintenance jobs

This keeps request validation, provider-specific behavior, and routing policy independently testable.

Alternative considered: a single-module service. Rejected because the router has enough moving parts that a flat implementation would become brittle quickly.

### Use a pluggable state store with SQLite as the intended durable backend
Phase 1 may use in-memory state for a minimal usable service, but the design targets SQLite for persisted inventory, health observations, cooldowns, manual overrides, and fallback accounting. The routing engine should therefore depend on a state-store interface rather than hardcoding persistence into the API layer.

Alternative considered: JSON files as the main durable state. Rejected because cooldowns, rolling health, and queryable inventory fit SQLite better and will be easier to inspect and evolve.

## Risks / Trade-offs

- [Phase 1 may ship with simpler routing than the final concept] -> Mitigate by keeping the API contract stable and making later stages additive behind the same aliases and endpoints.
- [Free provider inventories can change faster than static routing assumptions] -> Mitigate with explicit refresh hooks and early adapter boundaries so discovery logic can evolve without changing callers.
- [Adding persistence too early could slow initial delivery] -> Mitigate by keeping the state-store contract stable and deferring the SQLite implementation to a dedicated stage.
- [Zen endpoint-family metadata is not exposed directly by the Zen models API] -> Mitigate with a provider-side family cache plus controlled probing of alternate request families.
- [Some upstream formats may not expose clean first-text timing without streaming] -> Mitigate by recording best-effort first-text timing where supported and leaving it unset where it cannot be measured reliably.
- [Runtime integration can distract from service correctness] -> Mitigate by proving the standalone package first, then wiring it into the Hermes image in a later stage.

## Migration Plan

1. Create `packages/hermes-router` with a runnable local service and a stable API contract.
2. Add provider adapters and minimal free-first routing so the service can satisfy real requests using environment-provided local credentials for validation.
3. Add persistence, refresh loops, cooldown logic, and richer observability without changing the external API.
4. Wire the package into `flake.nix`, then into the Hermes runtime and service supervision model once standalone behavior is verified.
5. Adopt the router from Hermes profiles or other local tools only after the service is stable enough for opt-in use.

Rollback is straightforward in early stages because the router is additive: the package or runtime service can be disabled without changing existing Hermes profile configuration.

## Open Questions

- Should phase 1 accept only chat/completions-style requests, or should it reserve naming and schemas for future embeddings/responses-style endpoints?
- How much debug surface should exist before Prometheus-style metrics are added: JSON debug endpoints only, or text metrics from the start?
- Should runtime integration create a dedicated user service immediately, or first keep the package standalone for local/manual execution?
- Which specific free model should power any optional background bucketing or ranking workflow when that stage is added?
