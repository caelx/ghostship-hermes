## MODIFIED Requirements

### Requirement: Hermes runtime uses direct MiniMax primary with local router fallback
The Hermes image SHALL configure the managed Hermes runtime to use direct `opencode-go/minimax-m2.7` as its primary model path while keeping the local `ghostship-hermes-router` OpenAI-compatible API at `http://127.0.0.1:8788/v1` as the configured fallback endpoint.

#### Scenario: Managed Hermes config uses direct MiniMax primary
- **WHEN** the image bootstraps the managed Hermes config
- **THEN** the managed config sets `model.provider` to `opencode-go`
- **AND** the managed config sets `model.default` to `minimax-m2.7`

#### Scenario: Managed Hermes config uses router `agentic` fallback
- **WHEN** the image bootstraps the managed Hermes config
- **THEN** the managed config sets `fallback_model.provider` to `custom`
- **AND** the managed config sets `fallback_model.model` to `agentic`
- **AND** the managed config sets `fallback_model.base_url` to `http://127.0.0.1:8788/v1`
- **AND** the managed config sets `fallback_model.api_key_env` to `OPENAI_API_KEY`

### Requirement: Managed gateway starts with the local router available for fallback
The image SHALL keep the local router service available before the managed Hermes gateway starts so the configured fallback endpoint is ready if the direct primary lane fails.

#### Scenario: Router service starts before the managed gateway
- **WHEN** the container boots the managed Hermes services
- **THEN** `ghostship-hermes-router.service` is started before `ghostship-hermes-gateway.service`

### Requirement: Image and rollout validation prove direct-primary and router-fallback behavior
The repo's validation paths SHALL verify the direct-primary MiniMax contract, the router `agentic` fallback contract, the exact default blocked backend id, and the deployed gateway pidfile behavior instead of only checking older router-primary defaults.

#### Scenario: Smoke test verifies alias discovery and configured defaults
- **WHEN** maintainers run the Hermes image dashboard smoke test
- **THEN** the test verifies `ghostship-hermes-router.service` is active
- **AND** the test verifies the router model inventory exposes `auxiliary`, `coding`, `agentic`, `vision`, and `tts`
- **AND** the test verifies the managed Hermes config uses `provider = opencode-go` and `default = minimax-m2.7`
- **AND** the test verifies the managed Hermes config uses router alias `agentic` as the configured fallback model
- **AND** the test verifies the managed router environment includes `GHOSTSHIP_ROUTER_DISABLED_MODELS=openrouter/free`

#### Scenario: Published image and live host preserve the intended contract
- **WHEN** maintainers publish and deploy the Hermes image
- **THEN** the published image inspection verifies the managed config contains direct MiniMax primary and router `agentic` fallback
- **AND** the live host verifies the managed router env still disables the exact backend id `openrouter/free`
- **AND** the live host verifies `/home/hermes/.hermes/gateway.pid` remains present after `hermes doctor`
