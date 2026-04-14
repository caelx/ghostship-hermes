# live-image-runtime-gaps Specification

## Purpose
TBD - created by archiving change fix-live-image-runtime-gaps. Update Purpose after archive.
## Requirements
### Requirement: The published image must reflect the intended managed model contract
The published Hermes image SHALL configure the managed runtime to use direct `opencode-go/minimax-m2.7` as the primary model path and the local router `agentic` alias as the configured fallback path.

#### Scenario: Managed config uses direct MiniMax primary and router `agentic` fallback
- **WHEN** the image bootstraps the managed Hermes config
- **THEN** the managed config sets `model.provider` to `opencode-go`
- **AND** the managed config sets `model.default` to `minimax-m2.7`
- **AND** the managed config sets `fallback_model.provider` to `custom`
- **AND** the managed config sets `fallback_model.model` to `agentic`
- **AND** the managed config sets `fallback_model.base_url` to `http://127.0.0.1:8788/v1`
- **AND** the managed config sets `fallback_model.api_key_env` to `_GHOSTSHIP_ROUTER_API_KEY`

#### Scenario: Managed router env blocks only `openrouter/free` by default
- **WHEN** the managed router service environment is rendered
- **THEN** it includes `GHOSTSHIP_ROUTER_DISABLED_MODELS=openrouter/free`

### Requirement: The dashboard exposes the managed agent runtime contract
The dashboard SHALL expose enough managed agent configuration to validate the live primary model, fallback model, endpoint wiring, and gateway liveness state.

#### Scenario: Dashboard status includes primary and fallback config
- **WHEN** the dashboard reads the managed Hermes config
- **THEN** the status payload includes the managed primary model settings
- **AND** the status payload includes the managed fallback model settings
- **AND** the agent summary exposes the endpoint and liveness fields operators need to validate the runtime contract

#### Scenario: Dashboard browser flow opens a ttyd terminal successfully
- **WHEN** an operator opens a terminal from the dashboard UI
- **THEN** the dashboard creates an on-demand ttyd session
- **AND** the embedded terminal frame becomes reachable from the dashboard origin

### Requirement: Managed gateway liveness survives health inspection
The managed gateway SHALL keep `/home/hermes/.hermes/gateway.pid` present while the gateway service is running, including after `hermes doctor` inspects the runtime.

#### Scenario: `hermes doctor` does not remove the live managed gateway pidfile
- **WHEN** the managed gateway service is active and an operator runs `hermes doctor`
- **THEN** `/home/hermes/.hermes/gateway.pid` remains present afterward
- **AND** dashboard status continues to report the managed gateway marker as present

### Requirement: A healthy published image must prove the live runtime surface
The fix SHALL require post-publish and post-deploy validation instead of assuming source changes reached the deployed artifact.

#### Scenario: Published image and deployed host are inspected directly
- **WHEN** maintainers publish and deploy the Hermes image
- **THEN** they inspect the published image for the intended model/runtime contract
- **AND** they verify on the deployed host that the dashboard shows the intended config, terminal open works, the router env disables `openrouter/free`, and `gateway.pid` survives `hermes doctor`
- **AND** they do not treat the rollout as healthy if the direct `opencode-go` primary lane remains broken
