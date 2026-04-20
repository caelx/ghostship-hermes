## ADDED Requirements

### Requirement: Router supports discovered NVIDIA Build API inventory
The router SHALL support NVIDIA Build API as an optional first-class provider activated by `NVIDIA_BUILD_API_KEY`, but it SHALL discover the live NVIDIA catalog instead of relying on a repo-curated tuple. Only discovered NVIDIA endpoints that are marked free and remain eligible after repo-owned allow or block policy filters may become route candidates.

#### Scenario: Configured NVIDIA key activates discovered free inventory
- **WHEN** `NVIDIA_BUILD_API_KEY` is configured for the router
- **THEN** the router registers provider `nvidia-build` during provider construction and refresh
- **AND** the provider inventory comes from NVIDIA catalog discovery instead of a hardcoded repo tuple
- **AND** only discovered NVIDIA endpoints identified as free remain eligible for normal routing candidates

#### Scenario: Repo policy overlays shape discovered NVIDIA eligibility
- **WHEN** NVIDIA catalog discovery returns free endpoints that are not all acceptable for the repo's `agentic` lane
- **THEN** the router applies repo-owned usable or unused policy before final candidate selection
- **AND** discovered models explicitly marked unused do not become route candidates even if the provider exposes them as free

#### Scenario: Missing NVIDIA key leaves provider disabled
- **WHEN** `NVIDIA_BUILD_API_KEY` is not configured
- **THEN** the router does not register provider `nvidia-build`
- **AND** routing continues using the remaining configured providers without NVIDIA inventory

## MODIFIED Requirements

### Requirement: Router exposes only the `agentic` alias for normal routing
The router SHALL expose `agentic` as the only repo-supported logical alias for normal model selection and SHALL reject the retired logical aliases that previously represented other workload families.

#### Scenario: Model listing exposes only the supported alias
- **WHEN** a caller lists logical models from the router
- **THEN** the router exposes `agentic` as the only repo-supported alias for normal routing
- **AND** the router does not advertise the retired normal aliases `auxiliary`, `coding`, `vision`, or `tts`

#### Scenario: Retired logical alias is rejected
- **WHEN** a caller requests one of the retired normal logical aliases
- **THEN** the router returns an unsupported-model style error for that alias
- **AND** the router does not silently remap the request to a different logical alias

### Requirement: Router exposes uncategorized and unused discovered-model inventories
The router SHALL expose operator-facing inventory surfaces that distinguish discovered models that are not yet categorized from discovered models that are explicitly marked unused by repo policy.

#### Scenario: Uncategorized inventory lists discovered models awaiting review
- **WHEN** discovery finds eligible free models that are not present in the repo-owned usable rankings or the repo-owned unused-model lists
- **THEN** the router exposes those models through an uncategorized inventory surface
- **AND** those models do not become normal routing candidates

#### Scenario: Unused inventory lists explicitly excluded discovered models
- **WHEN** discovery finds free models that are explicitly present in the repo-owned unused-model lists
- **THEN** the router exposes those models through an unused inventory surface
- **AND** those models do not become normal routing candidates

### Requirement: Router performs free-first routing with transparent failover
The router SHALL perform free-first routing for the `agentic` alias by selecting the highest-priority provider that still has eligible candidates, keeping a top-five explicitly ranked usable set per provider, routing only across the highest-ranked three models from that five-model set that are currently eligible, retrying alternate models inside the same provider after retryable failures, and switching providers only after clear free-tier exhaustion evidence or the absence of eligible candidates on the current provider.

#### Scenario: Highest-priority provider with eligible models is selected first
- **WHEN** `nvidia-build`, `opencode-zen`, and `openrouter` all expose healthy eligible free candidates for `agentic`
- **THEN** the router selects `nvidia-build` ahead of `opencode-zen`
- **AND** the router selects `opencode-zen` ahead of `openrouter`
- **AND** lower-priority providers are not considered until the higher-priority provider becomes ineligible for normal routing

#### Scenario: Retryable model failure stays within the active provider
- **WHEN** the selected backend model on the active provider fails with a retryable non-exhaustion failure such as timeout, transport error, transient server error, or missing model
- **THEN** the router penalizes or cools down that concrete backend model
- **AND** it retries the request against the next eligible ranked model from the same provider before considering a lower-priority provider

#### Scenario: Cross-provider failover requires exhaustion evidence
- **WHEN** the active provider records explicit free-tier exhaustion evidence such as provider pacing, quota exhaustion, insufficient balance, repeated zero-output exhaustion, or equivalent exhaustion-class policy signals
- **THEN** the router marks that provider unavailable for normal routing according to the exhaustion policy
- **AND** it recomputes candidates from the next provider in priority order
- **AND** it does not switch providers for ordinary retryable non-exhaustion model failures alone

#### Scenario: Repeated pacing can escalate to probable daily exhaustion
- **WHEN** the active provider records repeated pacing, retry-after, or quota-like throttling signals across multiple request attempts or distinct backend models inside the configured suspect window
- **THEN** the router may classify that provider as probably exhausted for the current daily free window
- **AND** the router suppresses that provider for normal routing until recovery conditions or the configured reset window are reached
- **AND** the router exposes that suppression as inferred daily exhaustion instead of a generic transient cooldown

#### Scenario: Provider without eligible discovered candidates is skipped
- **WHEN** the highest-priority provider has no discovered free models that satisfy repo policy and `agentic` eligibility filtering
- **THEN** the router skips that provider for the current request
- **AND** it evaluates the next provider in the configured priority order

#### Scenario: Top-five reserve yields the best currently eligible three
- **WHEN** a provider has five explicitly ranked usable models in repo policy and one of the highest-ranked three is temporarily ineligible because of cooldown, model unavailability, or other non-exhaustion exclusion
- **THEN** the router promotes the next-ranked eligible model from that provider's top-five set into the active routing candidate set
- **AND** the active routing candidate set still contains at most three models

#### Scenario: Models outside the top-five usable set do not route
- **WHEN** a provider has explicitly ranked usable models below its top-five policy cutoff
- **THEN** those lower-ranked usable models remain visible in policy or debug surfaces
- **AND** they do not enter normal routing unless the operator changes the top-five usable set

#### Scenario: Uncategorized discovered models stay out of routing
- **WHEN** a provider discovers eligible free models that are not explicitly present in the usable rankings or the unused-model lists
- **THEN** those uncategorized models are excluded from normal routing
- **AND** routing continues using only the explicitly ranked usable candidates for that provider

#### Scenario: Pool exhaustion returns a router error
- **WHEN** every configured provider is either exhausted for free-tier routing or lacks eligible discovered `agentic` candidates
- **THEN** the router returns an error that indicates the `agentic` pool is currently exhausted or unavailable

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
The router SHALL preserve the state needed for unattended operation and SHALL expose enough health and debug information to explain discovered inventory, usable-policy inputs, active provider stickiness, and any exhaustion-driven provider switch.

#### Scenario: Routing state survives service restart
- **WHEN** the router process stops and starts again
- **THEN** persisted inventory, health observations, cooldowns, usable-policy overlays, and manual overrides remain available after restart

#### Scenario: Observability shows inventory classification and failover reason
- **WHEN** an operator inspects a candidate list, ranking surface, or route-debug surface
- **THEN** the router exposes whether each discovered model came from explicit usable ranking, explicit unused policy, or the uncategorized discovered set
- **AND** the router exposes whether a model or provider was excluded by unused policy, cooldown, or exhaustion policy
- **AND** the router exposes the exact reason when routing moved from one provider to the next

#### Scenario: Observability distinguishes daily exhaustion from short cooldown
- **WHEN** a provider has been suppressed because of inferred daily-limit exhaustion
- **THEN** router state or debug surfaces expose that the provider is considered probably exhausted for the daily free window
- **AND** those surfaces expose the evidence summary, the current reset or probe deadline, and the next recovery condition

#### Scenario: Observability exposes uncategorized inventory and stickiness
- **WHEN** an operator inspects router state, route-debug surfaces, or ranking-debug surfaces
- **THEN** the router exposes uncategorized and explicitly unused discovered inventories
- **AND** the router exposes whether session stickiness affected the final selection
- **AND** the router exposes enough information to explain why the router stayed on or left the previously selected provider or model

#### Scenario: Metrics endpoint exposes provider-exhaustion behavior
- **WHEN** an operator scrapes the router metrics endpoint after an exhaustion-driven provider switch
- **THEN** the router exposes metrics for provider exhaustion, provider suppression, same-provider retries, and cross-provider failover counts
- **AND** those metrics distinguish exhaustion-driven provider changes from model-local retry behavior

### Requirement: Router behavior is configurable without code changes
The router SHALL support operator configuration for provider enablement, strict provider priority, discovery policy, free-only filtering, usable-model rankings, unused-model policy, and exhaustion thresholds without requiring source edits.

#### Scenario: Configuration changes affect future routing decisions
- **WHEN** the operator updates supported router configuration for provider enablement, provider order, discovery policy, usable ranking policy, unused-model policy, or exhaustion thresholds
- **THEN** future `agentic` routing decisions reflect the updated policy without requiring application code changes

#### Scenario: Daily-limit inference policy is configurable
- **WHEN** the operator updates provider-specific suspect windows, daily-reset assumptions, pacing thresholds, or exhaustion evidence thresholds
- **THEN** future provider-exhaustion classification follows the updated policy without requiring application code changes

#### Scenario: Durable operator overrides affect ranking and eligibility
- **WHEN** the operator applies a persistent override for model or provider disablement, ranked ordering, or unused-model policy
- **THEN** future discovery, ranking, and routing decisions reflect that override
- **AND** the override remains visible and durable across service restarts
