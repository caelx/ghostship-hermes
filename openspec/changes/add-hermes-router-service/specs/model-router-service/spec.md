## ADDED Requirements

### Requirement: Router exposes stable logical model aliases through a local API
The router SHALL expose a stable localhost API that presents logical model aliases instead of requiring callers to know current upstream backend model names.

#### Scenario: Logical aliases are discoverable
- **WHEN** a caller lists available models from the router
- **THEN** the response includes stable logical aliases for at least `lightweight`, `coding`, and `heavyweight`
- **AND** those aliases remain stable even when the underlying backend inventory changes

#### Scenario: Inference requests accept a logical alias
- **WHEN** a caller sends a chat/completions-style request that names a logical alias
- **THEN** the router accepts the alias as the requested model identifier
- **AND** the router resolves that alias to a concrete backend internally

### Requirement: Router performs free-first routing with transparent failover
The router SHALL prefer eligible free backends for each logical alias, retry alternate candidates after retryable failures, and surface an error only after the candidate pool and fallback policy are exhausted.

#### Scenario: Healthy free candidate is selected before paid fallback
- **WHEN** a caller requests a logical alias with at least one eligible healthy free candidate
- **THEN** the router attempts a healthy free candidate before any paid fallback

#### Scenario: Retryable backend failure triggers transparent retry
- **WHEN** the selected backend fails with a retryable failure such as timeout, rate limit, transient provider error, or missing model
- **THEN** the router penalizes or cools down that backend
- **AND** it retries the request against the next eligible candidate without requiring caller intervention

#### Scenario: Pool exhaustion returns a router error
- **WHEN** all eligible candidates for the requested alias are unusable and no fallback candidate is allowed or available
- **THEN** the router returns an error that indicates the alias pool is currently exhausted or unavailable

### Requirement: Router supports explicit Gemini fallback
The router SHALL treat Gemini as a stable fallback tier that is selected only when the free pool is unusable or cannot satisfy the request.

#### Scenario: Gemini fallback is used after free-pool exhaustion
- **WHEN** a caller requests a logical alias and the router determines that no eligible free candidate can satisfy the request
- **THEN** the router may route the request to the configured Gemini fallback
- **AND** the routing result records that paid fallback was used

#### Scenario: Gemini is not preferred over a healthy free candidate
- **WHEN** at least one eligible healthy free candidate is available for the requested logical alias
- **THEN** the router does not select Gemini first

### Requirement: Router maintains backend inventory outside the request hot path
The router SHALL discover and maintain backend inventory through startup and background refresh workflows instead of requiring manual hardcoded model updates for normal operation.

#### Scenario: Startup and scheduled refresh update inventory
- **WHEN** the router starts or a scheduled refresh workflow runs
- **THEN** the router refreshes its provider and model inventory
- **AND** later routing decisions use that refreshed inventory without requiring a service restart

#### Scenario: Stale model failure triggers refresh
- **WHEN** a request fails because the selected backend model no longer exists
- **THEN** the router triggers an inventory refresh workflow
- **AND** later requests use refreshed inventory instead of continuing to rely on the missing model

### Requirement: Optional model-assisted bucketing and ranking stays free-first
If the router uses model-assisted background classification or ranking, it SHALL use a configured free model rather than the Gemini fallback tier.

#### Scenario: Background bucketing uses a free model
- **WHEN** the router performs model-assisted background bucketing or ranking
- **THEN** it uses a configured free model path for that maintenance workflow
- **AND** it does not consume Gemini as part of routine bucketing or ranking work

### Requirement: Router persists routing state and exposes observability surfaces
The router SHALL preserve the state needed for unattended operation and expose enough health and debug information to explain routing behavior.

#### Scenario: Routing state survives service restart
- **WHEN** the router process stops and starts again
- **THEN** persisted inventory, health observations, cooldowns, bucket assignments, and manual overrides remain available after restart

#### Scenario: Operator can inspect router health and behavior
- **WHEN** an operator checks the router's health, readiness, logs, or debug surfaces
- **THEN** the router exposes current health state, backend choices, failure reasons, and fallback activity

### Requirement: Router behavior is configurable without code changes
The router SHALL support operator configuration for providers, alias buckets, refresh behavior, cooldown thresholds, routing weights, fallback policy, and allow or block controls without requiring source edits.

#### Scenario: Configuration changes affect future routing decisions
- **WHEN** the operator updates supported router configuration for provider enablement, weights, bucket rules, cooldown thresholds, or fallback policy
- **THEN** future routing decisions reflect the updated policy without requiring application code changes
