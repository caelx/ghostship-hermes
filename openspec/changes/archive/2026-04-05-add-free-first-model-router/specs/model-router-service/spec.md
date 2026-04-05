## ADDED Requirements

### Requirement: Shared router service runs as a persistent workstation service
The workstation SHALL run the model router as a long-lived shared service under the persisted `hermes` user `systemd` manager so it is available to any local profile or tool without creating per-profile router instances.

#### Scenario: Router starts with the shared workstation runtime
- **WHEN** the workstation runtime seeds and starts its managed user services
- **THEN** the model router service is installed as a repo-managed `hermes` user unit
- **AND** the service starts automatically under the shared user manager

#### Scenario: Router survives restart and state reuse
- **WHEN** the container or `hermes` user manager restarts
- **THEN** the model router service is started again automatically
- **AND** the router reuses its persisted state rather than starting from an empty inventory and health history

### Requirement: Router exposes stable logical model aliases through a local API
The router SHALL expose a stable localhost API that presents logical model aliases instead of requiring callers to know the current upstream backend model names.

#### Scenario: Logical aliases are discoverable
- **WHEN** a caller lists available models from the router
- **THEN** the response includes stable logical aliases for at least `lightweight`, `coding`, and `heavyweight`
- **AND** the aliases remain stable even when the underlying backend inventory changes

#### Scenario: Inference requests use a logical alias
- **WHEN** a caller sends a chat/completions-style request that names a logical alias
- **THEN** the router accepts the alias as the requested model identifier
- **AND** the router resolves the alias to a concrete backend internally

### Requirement: Router maintains backend inventory outside the request hot path
The router SHALL discover and maintain backend model inventory through startup and background refresh workflows instead of requiring manual hardcoded model updates for normal operation.

#### Scenario: Router refreshes inventory on startup and on a timer
- **WHEN** the router starts or its refresh timer runs
- **THEN** the router refreshes its provider/model inventory
- **AND** the refreshed inventory becomes available for later routing decisions without restarting the service

#### Scenario: Router recovers from stale model inventory
- **WHEN** a request fails because the selected backend model no longer exists
- **THEN** the router triggers an inventory refresh workflow
- **AND** later requests use the refreshed inventory instead of continuing to rely on the missing model

### Requirement: Router performs free-first routing with transparent failover
The router SHALL prefer free backends for each logical alias, transparently retry alternate candidates when a backend fails, and surface an error only after the candidate pool is exhausted or an explicit fallback policy is reached.

#### Scenario: Healthy free candidate is selected first
- **WHEN** a caller requests a logical alias with multiple eligible free candidates
- **THEN** the router ranks the eligible candidates using its stored routing state
- **AND** it attempts the highest-ranked healthy free candidate before any paid fallback

#### Scenario: Router retries after backend failure
- **WHEN** the selected backend fails with a retryable failure such as timeout, rate limit, transient provider error, or model missing
- **THEN** the router penalizes or cools down that backend immediately
- **AND** it retries the request against the next eligible candidate without requiring caller intervention

#### Scenario: Router surfaces exhaustion only after all options are unusable
- **WHEN** all eligible free candidates have failed and no fallback candidate is allowed or available
- **THEN** the router returns an error to the caller
- **AND** the error indicates that the logical pool is currently exhausted or unavailable

### Requirement: Router supports Gemini as the explicit paid fallback tier
The router SHALL treat Gemini as a stable fallback tier that is used only when the free pool is unusable or lacks the required capability.

#### Scenario: Gemini fallback is used after free exhaustion
- **WHEN** a caller requests a logical alias and the router determines that no eligible free candidate can satisfy the request
- **THEN** the router may route the request to the configured Gemini fallback
- **AND** the routing result records that paid fallback was used

#### Scenario: Gemini is not preferred over healthy free models
- **WHEN** at least one eligible healthy free candidate is available for the requested logical alias
- **THEN** the router does not select Gemini first
- **AND** Gemini remains reserved for fallback behavior

### Requirement: Router persists routing state and exposes observability surfaces
The router SHALL persist the state it needs for unattended operation and expose enough observability to explain routing behavior, failures, and fallback decisions.

#### Scenario: Routing state survives service restart
- **WHEN** the router process stops and starts again
- **THEN** persisted inventory, health observations, cooldowns, bucket assignments, and manual overrides remain available after restart
- **AND** the router can continue ranking backends using that restored state

#### Scenario: Operator can inspect router behavior
- **WHEN** an operator checks the router's health, readiness, logs, or debug endpoints
- **THEN** the router exposes current health state, backend choices, retry/failure reasons, and fallback activity
- **AND** the observability surface is sufficient to diagnose unhealthy providers or poor ranking outcomes

### Requirement: Router behavior is configurable without code changes
The router SHALL support operator configuration for providers, refresh intervals, bucket definitions, weights, cooldown behavior, fallback behavior, and allow/block controls without requiring code edits.

#### Scenario: Operator changes routing policy through configuration
- **WHEN** the operator updates router configuration for weights, bucket rules, cooldown thresholds, or provider enablement
- **THEN** the router applies the updated policy through its supported configuration path
- **AND** future routing decisions reflect the new policy without source-code modification
