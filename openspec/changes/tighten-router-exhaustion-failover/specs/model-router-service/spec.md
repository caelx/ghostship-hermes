## MODIFIED Requirements

### Requirement: Router performs free-first routing with transparent failover
The router SHALL prefer eligible free backends for each logical alias, track health at the concrete backend-model level, retry alternate models after retryable failures, and surface an error only after the candidate pool is exhausted.

#### Scenario: Healthy free candidate is selected before paid fallback
- **WHEN** a caller requests a logical alias with at least one eligible healthy free candidate
- **THEN** the router attempts a healthy free candidate before any paid fallback

#### Scenario: Retryable backend failure triggers transparent retry
- **WHEN** the selected backend fails with a retryable failure such as timeout, rate limit, transient provider error, or missing model
- **THEN** the router penalizes or cools down that concrete backend model
- **AND** it retries the request against the next eligible backend model without requiring caller intervention

#### Scenario: Exhaustion retry re-enters ranked candidate selection
- **WHEN** a backend fails with an exhaustion-class signal such as provider throttling, quota exhaustion, or insufficient balance
- **THEN** the router updates exhaustion state for that concrete backend model
- **AND** it recomputes the remaining eligible candidates from the ranked priority list
- **AND** it continues the same request with the highest-ranked remaining candidate regardless of provider

#### Scenario: Pool exhaustion returns a router error
- **WHEN** all eligible backend-model candidates for the requested alias are unusable
- **THEN** the router returns an error that indicates the alias pool is currently exhausted or unavailable

#### Scenario: Startup routing uses deterministic ordering without assisted ranking calls
- **WHEN** the router starts and performs its initial inventory refresh
- **THEN** it orders candidates with deterministic heuristic scoring plus any persisted ranking data already stored in router state
- **AND** it does not send worker-assisted ranking calls during the startup refresh path

#### Scenario: Candidate ordering uses persisted ranking and recent health when available
- **WHEN** the router orders eligible candidates for a logical alias after startup
- **THEN** it combines free-model preference, alias fit, rolling live health data, deterministic heuristics, and any persisted ranking outputs
- **AND** it does not require a fresh assisted ranking pass before requests can route

#### Scenario: Provider-wide suppression affects candidate selection
- **WHEN** a provider enters temporary cooldown or disablement because of broad auth, timeout, rate-limit, or exhaustion signals
- **THEN** the router deprioritizes or excludes models from that provider during candidate selection
- **AND** the provider becomes eligible again after recovery conditions or cooldown expiry

### Requirement: Router maintains provider-wide health state
The router SHALL track provider-wide health independently from concrete-model health so it can react to broad provider issues without waiting for every model to fail independently.

#### Scenario: Broad provider failures trigger provider cooldown
- **WHEN** repeated recent failures indicate that many requests or refreshes against a provider are failing for the same systemic reason
- **THEN** the router records provider-wide degraded state and applies a temporary cooldown or disablement to that provider

#### Scenario: Temporary throttle uses provider pacing before provider disablement
- **WHEN** a provider returns a temporary throttle signal such as a `429` with `Retry-After` or an explicit upstream temporary rate-limit message
- **THEN** the router applies provider-scoped pacing to that provider lane using the retry guidance when available
- **AND** it uses a base minimum spacing of `3 seconds` for OpenRouter and `2 seconds` for OpenCode Zen between requests to the same provider
- **AND** it does not immediately convert that signal into a six-hour provider disablement unless stronger provider-wide evidence appears

#### Scenario: Explicit balance or hard quota exhaustion triggers long provider disablement
- **WHEN** a provider returns explicit balance exhaustion, hard quota exhaustion, or another non-temporary exhaustion signal
- **THEN** the router treats the provider as broadly unavailable
- **AND** it disables that provider for at least six hours

#### Scenario: Provider exhaustion evidence survives cross-provider attempts
- **WHEN** one backend model on a provider records a recent exhaustion failure
- **AND** a later attempt within the suspect window reaches another backend model on that same provider after trying another provider in between
- **AND** the later backend model also fails with a qualifying exhaustion signal
- **THEN** the router still applies provider-wide exhaustion logic to that original provider

#### Scenario: Provider recovery uses probe admission
- **WHEN** a provider-wide exhaustion disablement expires
- **THEN** the router re-admits that provider through a probe-style recovery path
- **AND** only a failed recovery probe or another strong exhaustion signal may re-disable it for a longer window

### Requirement: Router stores rolling health and performance windows
The router SHALL maintain recent health and timing data that is suitable for ranking volatile free-model inventories.

#### Scenario: Recent behavior outweighs lifetime totals
- **WHEN** the router evaluates a candidate model or provider
- **THEN** recent rolling latency, failure, rate-limit, and success signals influence ranking more strongly than long-lived aggregate counters

#### Scenario: Likely free-tier exhaustion affects ranking
- **WHEN** recent failure patterns suggest probable free-tier exhaustion for a model or provider
- **THEN** the router penalizes that candidate or provider until recovery signals appear

#### Scenario: Model exhaustion cooldowns escalate across consecutive failures
- **WHEN** the same provider-model pair records repeated consecutive exhaustion failures without an intervening success
- **THEN** the router increases that model's cooldown through an escalating ladder
- **AND** the ladder includes at least `30 seconds`, `1 minute`, `5 minutes`, and `10 minutes` before later capped escalation

#### Scenario: Retry guidance influences provider pacing and cooldown
- **WHEN** an exhaustion response includes provider retry guidance such as `Retry-After`
- **THEN** the router uses that guidance as an input to the next pacing or cooldown decision for the affected provider lane
- **AND** it does not shorten the delay below the configured provider spacing floor for that provider

#### Scenario: Successful model call resets exhaustion escalation
- **WHEN** a provider-model pair succeeds after an exhaustion-driven cooldown period
- **THEN** the router resets or clears that model's consecutive exhaustion escalation state

### Requirement: Router persists routing state and exposes observability surfaces
The router SHALL preserve the state needed for unattended operation and expose enough health and debug information to explain routing behavior.

#### Scenario: Routing state survives service restart
- **WHEN** the router process stops and starts again
- **THEN** persisted inventory, health observations, cooldowns, bucket assignments, and manual overrides remain available after restart

#### Scenario: Operator can inspect router health and behavior
- **WHEN** an operator checks the router's health, readiness, logs, or debug surfaces
- **THEN** the router exposes current health state, backend choices, model-level failure reasons, and timing data

#### Scenario: Time-to-first-text is recorded when available
- **WHEN** the selected upstream protocol makes first returned text observable
- **THEN** the router records best-effort time-to-first-text for that concrete backend model
- **AND** debug or state surfaces include that timing alongside total latency

#### Scenario: Metrics endpoint exposes routing and ranking health
- **WHEN** an operator scrapes the router metrics endpoint
- **THEN** the router exposes request, failover, refresh, cooldown, latency, and ranking metrics in a stable machine-readable format

#### Scenario: Observability shows ranking rationale
- **WHEN** an operator inspects a candidate list or ranking debug surface
- **THEN** the router exposes the current ranking score, health-derived score inputs, and any active override or cooldown state for each candidate

#### Scenario: Observability exposes suppression source
- **WHEN** an operator inspects router debug or metrics surfaces after throttling or exhaustion-driven failover
- **THEN** the router exposes whether the affected backend is unavailable because of provider pacing, model cooldown, temporary provider throttle handling, or hard provider disablement

### Requirement: Router behavior is configurable without code changes
The router SHALL support operator configuration for providers, alias buckets, refresh behavior, cooldown thresholds, routing weights, fallback policy, and allow or block controls without requiring source edits.

#### Scenario: Configuration changes affect future routing decisions
- **WHEN** the operator updates supported router configuration for provider enablement, weights, bucket rules, cooldown thresholds, or fallback policy
- **THEN** future routing decisions reflect the updated policy without requiring application code changes

#### Scenario: Durable operator overrides affect ranking and eligibility
- **WHEN** the operator applies a persistent override for model or provider disablement, weighting, or alias pinning
- **THEN** future routing and ranking decisions reflect that override
- **AND** the override remains visible and durable across service restarts

#### Scenario: Provider credential precedence is explicit
- **WHEN** the router loads provider credentials from environment variables
- **THEN** OpenRouter uses `OPENROUTER_API_KEY`
- **AND** OpenCode Zen prefers `OPENCODE_GO_API_KEY` over `OPENCODE_API_KEY` when both are present

#### Scenario: Exhaustion cooldown, provider pacing, and provider breaker policy is configurable
- **WHEN** the operator updates exhaustion ladder, provider spacing, suspect-window, provider-disable, or probe-recovery configuration
- **THEN** future exhaustion handling follows the updated policy without changing application code

#### Scenario: Router alternates ranked provider lanes
- **WHEN** the router builds candidates for a logical alias
- **THEN** it ranks the top three eligible models for each provider separately
- **AND** transparent failover alternates between provider lanes before revisiting lower-ranked models on the same provider
