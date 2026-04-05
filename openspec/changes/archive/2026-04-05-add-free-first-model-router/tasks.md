## 1. Router package and runtime scaffolding

- [ ] 1.1 Create the router package/module structure and choose the Python service stack, dependency set, and repository location for the long-lived router implementation.
- [ ] 1.2 Add persisted router config/state path conventions, including SQLite storage, journald-friendly logging, and any repo-managed default configuration files.
- [ ] 1.3 Add the shared `hermes` user `systemd` service unit and any companion refresh timer/service needed to start the router with the workstation runtime.

## 2. Local API and provider integration

- [ ] 2.1 Implement the localhost API surface for logical model aliases, model listing, chat/completions-style inference, and health/readiness endpoints.
- [ ] 2.2 Implement provider adapter contracts and initial provider integrations for free-model discovery/inference plus Gemini fallback inference.
- [ ] 2.3 Implement router configuration loading for providers, alias buckets, weights, cooldown thresholds, fallback policy, and allow/block controls.

## 3. Routing engine and persistence

- [ ] 3.1 Implement the SQLite-backed registry/state layer for inventory, provider metadata, health observations, cooldowns, bucket assignments, and operator overrides.
- [ ] 3.2 Implement background inventory refresh, startup refresh, forced refresh on stale-model failures, and bucket classification outside the request hot path.
- [ ] 3.3 Implement free-first candidate ranking, retry/failover behavior, normalized error handling, cooldown updates, and explicit Gemini fallback accounting.

## 4. Verification and documentation

- [ ] 4.1 Add unit and integration coverage for alias discovery, refresh behavior, failover, cooldowns, paid fallback, and restart-state restoration.
- [ ] 4.2 Validate service wiring in the workstation runtime so the router starts under the shared user manager and is reachable on localhost after bootstrap.
- [ ] 4.3 Document router configuration, endpoints, persistence, and operational debugging in `README.md`, `CHANGELOG.md`, and any router-specific docs needed for maintainers.
