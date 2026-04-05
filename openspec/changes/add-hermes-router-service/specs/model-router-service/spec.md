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
The router SHALL prefer eligible free backends for each logical alias, track health at the concrete backend-model level, retry alternate models after retryable failures, and surface an error only after the candidate pool is exhausted.

#### Scenario: Healthy free candidate is selected before paid fallback
- **WHEN** a caller requests a logical alias with at least one eligible healthy free candidate
- **THEN** the router attempts a healthy free candidate before any paid fallback

#### Scenario: Retryable backend failure triggers transparent retry
- **WHEN** the selected backend fails with a retryable failure such as timeout, rate limit, transient provider error, or missing model
- **THEN** the router penalizes or cools down that concrete backend model
- **AND** it retries the request against the next eligible backend model without requiring caller intervention

#### Scenario: Pool exhaustion returns a router error
- **WHEN** all eligible backend-model candidates for the requested alias are unusable
- **THEN** the router returns an error that indicates the alias pool is currently exhausted or unavailable

### Requirement: Router refreshes inventory from OpenRouter and OpenCode Zen
The router SHALL maintain candidate inventory from both OpenRouter and OpenCode Zen so alias routing and model-level failover can use either provider.

#### Scenario: Startup and scheduled refresh update both provider inventories
- **WHEN** the router starts or a scheduled refresh workflow runs
- **THEN** it refreshes both OpenRouter and OpenCode Zen inventories when credentials are configured
- **AND** later routing decisions use the combined refreshed inventory without requiring a service restart

### Requirement: Router supports mixed OpenCode Zen endpoint families
The router SHALL be able to invoke OpenCode Zen models across the endpoint families required by those models while keeping the local router API stable for callers.

#### Scenario: Zen model uses a non-chat upstream endpoint family
- **WHEN** the router selects an OpenCode Zen model that requires `/responses`, `/messages`, or a Google-style model endpoint
- **THEN** the router transforms the local chat-completions request into the correct upstream format
- **AND** it normalizes the upstream response back into the local chat-completions response shape

#### Scenario: Zen endpoint family is learned per model
- **WHEN** the router does not yet know which endpoint family a specific Zen model requires
- **THEN** the router may probe acceptable upstream formats for that model
- **AND** it caches the working endpoint family for later requests

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
If the router uses model-assisted background classification or ranking, it SHALL use a configured free model.

#### Scenario: Background bucketing uses a free model
- **WHEN** the router performs model-assisted background bucketing or ranking
- **THEN** it uses a configured free model path for that maintenance workflow
- **AND** it does not consume a paid fallback model as part of routine bucketing or ranking work

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

### Requirement: Router behavior is configurable without code changes
The router SHALL support operator configuration for providers, alias buckets, refresh behavior, cooldown thresholds, routing weights, fallback policy, and allow or block controls without requiring source edits.

#### Scenario: Configuration changes affect future routing decisions
- **WHEN** the operator updates supported router configuration for provider enablement, weights, bucket rules, cooldown thresholds, or fallback policy
- **THEN** future routing decisions reflect the updated policy without requiring application code changes
