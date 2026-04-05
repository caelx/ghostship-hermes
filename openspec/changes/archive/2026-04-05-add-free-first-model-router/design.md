## Context

The Ghostship Hermes workstation already runs shared long-lived services under the persisted `hermes` user `systemd` manager, with repo-managed units seeded into `~/.config/systemd/user` and state persisted through the managed home facade. The proposed router fits that runtime model: it is not profile-scoped, does not require root privileges, and should be available as a stable localhost service for any Hermes profile or other local tool that chooses to use it.

The router must hide volatile free-model provider behavior behind a stable API. That means its architecture needs to separate the request path from slower maintenance work such as model discovery and bucket classification. It also needs a durable local state store so health scoring, cooldowns, and operator overrides survive restarts instead of resetting to an optimistic empty state.

## Goals / Non-Goals

**Goals:**
- Run a shared long-lived router as a persisted `hermes` user service.
- Expose a stable local API with logical aliases such as `lightweight`, `coding`, and `heavyweight`.
- Keep model discovery, ranking, cooldowns, and failover inside the router rather than leaking provider volatility to callers.
- Persist router state, configuration-derived overrides, and health observations across restarts.
- Provide structured logs, health/readiness endpoints, and debug-friendly metrics surfaces.

**Non-Goals:**
- Automatically reconfigure Hermes profiles or make the router the default model endpoint.
- Build a browser UI for router administration in the first change.
- Solve advanced task classification with heavyweight online inference in the request path.
- Introduce privileged networking, root services, or profile-specific router instances.

## Decisions

### Run the router as a shared `hermes` user `systemd` service
The router will be installed as a repo-managed user unit in the same persisted user-manager model used by the dashboard and other workstation services. This matches the workstation runtime contract, keeps the service available across restarts, and avoids adding a second service-management pattern.

Alternative considered: a root-level system service. Rejected because the router does not need privileged startup ordering or privileged ports, and the workstation standard is to keep long-lived agent-facing services under the persisted `hermes` user manager.

### Expose an OpenAI-compatible localhost API with stable logical model aliases
The router API should include `/v1/models`, a chat/completions-style inference endpoint, and health/readiness endpoints. Logical aliases such as `lightweight`, `coding`, and `heavyweight` will appear as stable model IDs to callers, while the router resolves those aliases to backend providers internally.

Alternative considered: inventing a custom router-specific API. Rejected because the router is meant to be easy for Hermes and other local tools to adopt, and an OpenAI-compatible surface minimizes adapter work while preserving the router's internal freedom.

### Split the service into hot-path routing and background maintenance loops
The request-serving process will read from a local registry/state store and make routing decisions synchronously, while discovery, classification, recovery probing, and inventory refresh run on startup and on timers. Forced refresh may also be triggered by request-path evidence such as model-not-found responses, but the expensive work still happens outside the primary ranking path.

Alternative considered: doing discovery and classification inline during each request. Rejected because it adds latency and makes free-provider instability directly visible to callers.

### Use a local SQLite-backed state store for inventory and router state
SQLite is the right persistence layer for a single-node container-local service: simple deployment, crash-safe durability, no separate daemon, and enough structure to store model inventory, provider metadata, rolling health counters, cooldowns, bucket assignments, and operator overrides. The router can also write structured logs to stdout/stderr for journald capture while using SQLite for queryable state.

Alternative considered: flat JSON files only. Rejected because the router needs durable rolling state with concurrent reads, periodic writes, and queryable health/ranking data that will quickly become awkward and fragile in ad hoc files.

### Model providers use adapter plugins with uniform error normalization
Each upstream provider will implement a small adapter contract for model listing, capability metadata extraction, and inference invocation. Provider-specific failures will be normalized into router error categories such as `rate_limited`, `unauthorized`, `timeout`, `server_error`, and `model_missing`, which the routing engine can score consistently.

Alternative considered: embedding provider-specific logic directly in the routing engine. Rejected because it couples the core ranking/failover logic to every provider and makes it harder to add or tune providers independently.

### Free-first routing uses scored candidates with immediate penalties and cooldowns
For each logical alias, the router will assemble candidates from the registry, remove disabled or cooling-down entries, sort by a composite score, and attempt the best candidate first. Failures immediately update state: repeated rate limits and quota-like signals trigger longer cooldowns, timeouts lower score and may trigger temporary disablement, and provider/model auth failures mark the backend unavailable until configuration or operator action changes.

Alternative considered: round-robin selection among all matching free models. Rejected because the spec explicitly prioritizes health, responsiveness, and depletion awareness rather than equal distribution.

### Keep Gemini as an explicit stable fallback tier, not part of the free-model competition
Gemini will live in the routing policy as a final fallback candidate class. It should not be scored against volatile free pools on every request; instead, the free pool is exhausted first and Gemini is selected only when free options are unavailable, unhealthy, or missing required capability coverage.

Alternative considered: mixing Gemini directly into the ranked candidate set. Rejected because it would blur the free-first policy and make fallback behavior harder to reason about and tune.

## Risks / Trade-offs

- [Free-provider inventories and metadata are volatile] -> Mitigate with startup refresh, timer refresh, forced refresh on model-missing failures, and graceful fallback when discovery data is stale.
- [Heuristic bucket assignment may misclassify models] -> Mitigate with operator override support, stored manual assignments, and initial simple heuristics that can be replaced later.
- [Shared global state can let one noisy workload distort routing for others] -> Mitigate with rolling windows, capped penalties, and clear observability so operators can tune thresholds.
- [Fallback to paid Gemini can hide free-pool quality problems] -> Mitigate with explicit logs/metrics when fallback occurs and counters that distinguish free success from paid rescue.
- [A single shared service is a single point of failure] -> Mitigate with `systemd` restart policy, readiness endpoints, persistent state recovery, and keeping the hot path small.

## Migration Plan

1. Add the router code, packaging, repo-managed user unit, and any supporting refresh timer/service.
2. Start the router automatically as part of the shared workstation runtime so it is available on localhost after bootstrap.
3. Verify the service independently through health, readiness, model-list, and simulated failover tests.
4. Leave Hermes profile configuration unchanged in this change; adoption by callers remains opt-in and can be handled by later work.
5. Roll back by disabling the repo-managed user unit and removing the router package/state wiring without changing profile configuration.

## Open Questions

- Which exact provider set should be included in phase 1 beyond Gemini fallback and the first free-model source?
- Should metrics be exposed only as JSON debug endpoints initially, or as Prometheus-compatible text from the start?
- Should operator overrides live entirely in the SQLite state store, in a persisted config file, or in a layered combination of both?
