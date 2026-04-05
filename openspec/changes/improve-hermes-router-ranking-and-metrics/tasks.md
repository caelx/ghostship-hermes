## 1. Rolling State And Metrics Foundations

- [x] 1.1 Extend router SQLite state to store rolling model and provider health windows, latency summaries, and ranking outputs
- [x] 1.2 Record recent success, failure, rate-limit, timeout, auth, total-latency, and first-text-latency observations during request handling
- [x] 1.3 Add a stable `GET /metrics` endpoint with Prometheus-formatted request, failover, refresh, cooldown, latency, and candidate metrics
- [x] 1.4 Add router tests that verify rolling-state persistence and metrics exposition

## 2. Provider Health And Recovery

- [x] 2.1 Add provider-wide health tracking and cooldown state alongside existing model-level penalties
- [x] 2.2 Update candidate selection to suppress or penalize providers in active cooldown while keeping model-level failover intact
- [x] 2.3 Detect likely provider-level exhaustion or systemic failure from recent request and refresh patterns
- [x] 2.4 Add tests that cover provider cooldown, recovery, and routing behavior during broad provider failures

## 3. Lightweight Free-Model Ranking

- [x] 3.1 Add a background ranking workflow that selects a healthy free model from the `lightweight` bucket as the ranking worker
- [x] 3.2 Persist coarse alias-fit scores, ranking reasons, and ranking confidence for concrete backend models
- [x] 3.3 Add selective reranking for top candidates per alias without placing model-assisted ranking in the request hot path
- [x] 3.4 Update candidate ordering to combine free-first eligibility, rolling health, learned ranking, and operator weights
- [x] 3.5 Add tests that cover ranking-worker selection, ranking persistence, and fallback to heuristic-only ordering when ranking data is absent

## 4. Overrides And Debug Surfaces

- [x] 4.1 Add durable override storage for model and provider disablement, weights, and alias pinning
- [x] 4.2 Expose ranking, provider-health, and per-model debug views that explain score inputs, cooldowns, and active overrides
- [x] 4.3 Wire router configuration for override defaults, ranking cadence, and provider-health thresholds without requiring code edits
- [x] 4.4 Add tests that verify overrides survive restart and affect routing and ranking decisions

## 5. Documentation And Validation

- [x] 5.1 Update router docs and changelog for metrics, provider health, lightweight-model ranking, and override behavior
- [x] 5.2 Run router-local test coverage, nix builds, and live smoke validation against configured OpenRouter and OpenCode Zen credentials
