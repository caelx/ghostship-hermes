## REMOVED Requirements

### Requirement: Hermes runtime uses the local router as its primary OpenAI-compatible endpoint
**Reason**: The managed image no longer treats the local router as the primary model endpoint.
**Migration**: Configure the managed runtime for direct `opencode-go/minimax-m2.7` primary execution and keep the local router only as the configured `fallback_model`.

### Requirement: Managed gateway starts behind the local router
**Reason**: The managed gateway no longer depends on a router-primary model contract.
**Migration**: Keep the managed gateway supervised by the repo-owned service contract, while the managed runtime uses direct primary execution and router fallback independently.

### Requirement: Image validation proves router-primary behavior
**Reason**: Validation must prove the current direct-primary contract instead of the retired router-primary contract.
**Migration**: Validate direct `opencode-go/minimax-m2.7` primary execution, router `agentic` fallback wiring, and absence of stale router-primary config drift.

## ADDED Requirements

### Requirement: Hermes runtime uses direct OpenCode Go as its primary model path
The Hermes image SHALL configure the managed Hermes runtime to use direct `opencode-go/minimax-m2.7` as the primary model lane while keeping the local `ghostship-hermes-router` OpenAI-compatible API as the configured fallback endpoint through alias `agentic`.

#### Scenario: Managed Hermes config uses direct primary and router fallback
- **WHEN** the image bootstraps the managed Hermes config
- **THEN** the managed config sets `model.provider` to `opencode-go`
- **AND** the managed config sets `model.default` to `minimax-m2.7`
- **AND** the managed config does not leave a router-primary `model.base_url` in place for the direct primary lane
- **AND** the managed config sets `fallback_model.provider` to `custom`
- **AND** the managed config sets `fallback_model.model` to `agentic`
- **AND** the managed config sets `fallback_model.base_url` to `http://127.0.0.1:8788/v1`
- **AND** the managed config sets `fallback_model.api_key_env` to `_GHOSTSHIP_ROUTER_API_KEY`

### Requirement: Managed config convergence removes retired router-primary drift
The image SHALL reconcile repo-owned managed config on boot so stale router-primary fields from older image generations do not continue shadowing the current direct-primary contract.

#### Scenario: Persisted router-primary base URL is removed during managed convergence
- **WHEN** the container boots with persisted `/home/hermes/.hermes/config.yaml` from an older router-primary image generation
- **THEN** managed convergence removes the retired root-managed `model.base_url` value that points at `http://127.0.0.1:8788/v1`
- **AND** the current direct-primary model contract remains in place after convergence

### Requirement: Image validation proves direct-primary behavior
The repo's image validation paths SHALL verify the direct-primary contract instead of accepting successful fallback-rescued replies as proof that the primary lane works.

#### Scenario: Validation proves the primary lane is not accidentally routed through fallback wiring
- **WHEN** maintainers run the Hermes image validation suite
- **THEN** the validation proves the managed primary runtime no longer inherits the retired router-primary `model.base_url`
- **AND** the validation proves a managed Hermes invocation can use the direct `opencode-go/minimax-m2.7` lane successfully
- **AND** the validation does not treat fallback-only success as proof that the primary lane is healthy
