## ADDED Requirements

### Requirement: Router supports curated NVIDIA Build API inventory
The router SHALL support NVIDIA Build API as an optional first-class provider activated by `NVIDIA_BUILD_API_KEY`. When enabled, the router SHALL expose only a repo-curated free-only NVIDIA inventory instead of broadly routing the hosted NVIDIA catalog.

#### Scenario: Configured NVIDIA key activates curated provider inventory
- **WHEN** `NVIDIA_BUILD_API_KEY` is configured for the router
- **THEN** the router registers provider `nvidia-build` during provider construction and refresh
- **AND** the provider inventory includes only repo-curated NVIDIA model ids
- **AND** only NVIDIA models designated free by the repo-owned inventory policy can become route candidates

#### Scenario: Missing NVIDIA key leaves provider disabled
- **WHEN** `NVIDIA_BUILD_API_KEY` is not configured
- **THEN** the router does not register provider `nvidia-build`
- **AND** routing continues using the remaining configured providers without NVIDIA inventory

## MODIFIED Requirements

### Requirement: Router performs free-first routing with transparent failover
The router SHALL prefer eligible free backends for each logical alias, cap each provider to its top scored alias-local candidates before cross-provider interleaving, track health at the concrete backend-model level, retry alternate models after retryable failures, and surface an error only after the candidate pool is exhausted.

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

#### Scenario: Candidate ordering uses persisted ranking and recent health
- **WHEN** the router orders eligible candidates for a logical alias
- **THEN** it combines free-model preference, alias fit, rolling live health data, and persisted ranking outputs
- **AND** it does not rely only on static name heuristics once ranking data is available

#### Scenario: Per-provider shortlist is capped before alias interleaving
- **WHEN** the router orders eligible candidates for a logical alias bucket
- **THEN** it keeps at most the top `3` scored models from each provider for that alias
- **AND** it interleaves the provider-local shortlists into the final alias candidate order
- **AND** lower-ranked models from the same provider do not enter normal routing for that alias unless operator pins or overrides explicitly require them

#### Scenario: Provider priority affects cross-provider ordering
- **WHEN** multiple providers expose healthy eligible candidates for the same logical alias
- **THEN** the router applies provider-priority policy after eligibility, cooldown, pacing, and health filtering
- **AND** `nvidia-build` ranks ahead of `opencode-zen` and `openrouter` by default when their remaining score inputs are otherwise comparable

#### Scenario: Provider-wide suppression affects candidate selection
- **WHEN** a provider enters temporary cooldown or disablement because of broad auth, timeout, rate-limit, or exhaustion signals
- **THEN** the router deprioritizes or excludes models from that provider during candidate selection
- **AND** the provider becomes eligible again after recovery conditions or cooldown expiry

### Requirement: Router maintains provider-wide health state
The router SHALL track provider-wide health independently from concrete-model health so it can react to broad provider issues without waiting for every model to fail independently.

#### Scenario: Broad provider failures trigger provider cooldown
- **WHEN** repeated recent failures indicate that many requests or refreshes against a provider are failing for the same systemic reason
- **THEN** the router records provider-wide degraded state and applies a temporary cooldown or disablement to that provider

#### Scenario: Distinct-model zero-output exhaustion trips provider disablement
- **WHEN** two distinct backend models on the same provider fail within the provider suspect window with exhaustion-class signals
- **AND** neither failure returns output to the caller
- **THEN** the router treats the provider as broadly exhausted
- **AND** it disables that provider for at least six hours

#### Scenario: Provider exhaustion evidence survives cross-provider attempts
- **WHEN** one backend model on a provider records a recent zero-output exhaustion failure
- **AND** a later attempt within the suspect window reaches a different backend model on that same provider after trying another provider in between
- **AND** the later backend model also fails with a zero-output exhaustion signal
- **THEN** the router still disables the original provider for the broad exhaustion window

#### Scenario: Provider recovers automatically after cooldown or refresh
- **WHEN** a provider cooldown expires or a later refresh succeeds
- **THEN** the router allows that provider to compete for routing again without manual intervention

#### Scenario: Provider recovery uses probe admission
- **WHEN** a provider-wide exhaustion disablement expires
- **THEN** the router re-admits that provider through a probe-style recovery path
- **AND** one immediate exhaustion probe failure can re-disable the provider with a longer cooldown

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

#### Scenario: Observability exposes exhaustion breaker state
- **WHEN** an operator inspects router debug or metrics surfaces after exhaustion-driven failover
- **THEN** the router exposes model exhaustion cooldown state, provider disablement state, and the current recovery or probe mode for affected providers

### Requirement: Router behavior is configurable without code changes
The router SHALL support operator configuration for providers, alias buckets, refresh behavior, cooldown thresholds, routing weights, fallback policy, and allow or block controls without requiring source edits.

#### Scenario: Configuration changes affect future routing decisions
- **WHEN** the operator updates supported router configuration for provider enablement, weights, bucket rules, cooldown thresholds, or fallback policy
- **THEN** future routing decisions reflect the updated policy without requiring application code changes

#### Scenario: Durable operator overrides affect ranking and eligibility
- **WHEN** the operator applies a persistent override for model or provider disablement, weighting, or alias pinning
- **THEN** future routing and ranking decisions reflect that override
- **AND** the override remains visible and durable across service restarts

#### Scenario: Exhaustion cooldown and provider breaker policy is configurable
- **WHEN** the operator updates exhaustion ladder, suspect-window, provider-disable, or probe-recovery configuration
- **THEN** future exhaustion handling follows the updated policy without changing application code
