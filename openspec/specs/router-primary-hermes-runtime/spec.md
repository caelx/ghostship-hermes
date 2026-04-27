## ADDED Requirements

### Requirement: Hermes runtime uses Ghostship Router as its primary model path
The Hermes image SHALL configure the managed Hermes runtime to use `custom:ghostship-router/deepseek-v4-pro` as the primary model lane, SHALL use `custom:ghostship-router/minimax-m2.7` as the configured fallback model lane, SHALL set `agent.reasoning_effort` to `high`, SHALL set `agent.max_turns` to `500`, and SHALL set the managed web backend to `firecrawl`.

#### Scenario: Managed Hermes config uses router primary and router fallback
- **WHEN** the image bootstraps the managed Hermes config
- **THEN** the managed config sets `model.provider` to `custom:ghostship-router`
- **AND** the managed config sets `model.default` to `deepseek-v4-pro`
- **AND** the managed config sets `fallback_model.provider` to `custom:ghostship-router`
- **AND** the managed config sets `fallback_model.model` to `minimax-m2.7`
- **AND** the managed config sets `web.backend` to `firecrawl`
- **AND** the managed config contains a `custom_providers` entry named `ghostship-router`
- **AND** that `custom_providers` entry sets `base_url` to `http://127.0.0.1:8788/v1`
- **AND** that `custom_providers` entry sets `api_key_env` to `_GHOSTSHIP_ROUTER_API_KEY`
- **AND** that `custom_providers` entry exposes `deepseek-v4-pro` and `minimax-m2.7`

### Requirement: Managed config convergence removes retired model-order drift
The image SHALL reconcile repo-owned managed config on boot so stale managed provider-order fields from older image generations do not continue shadowing the current router-primary contract.

#### Scenario: Persisted retired provider order is rewritten during managed convergence
- **WHEN** the container boots with persisted `/home/hermes/.hermes/config.yaml` from an older image generation
- **THEN** managed convergence removes any retired root-managed `model.base_url` value that points at `http://127.0.0.1:8788/v1`
- **AND** managed convergence rewrites the managed primary model contract to `custom:ghostship-router/deepseek-v4-pro`
- **AND** managed convergence rewrites the managed fallback model contract to `custom:ghostship-router/minimax-m2.7`
- **AND** managed convergence rewrites the managed web backend to `firecrawl`
- **AND** managed convergence sets the managed `agent.reasoning_effort` default to `high`
- **AND** managed convergence sets the managed `agent.max_turns` default to `500`

### Requirement: Image validation proves router-primary behavior
The repo's image validation paths SHALL verify the router-primary contract instead of accepting stale config text as proof that the managed model order is correct.

#### Scenario: Validation proves the runtime no longer uses the retired provider order
- **WHEN** maintainers run the Hermes image validation suite
- **THEN** the validation proves the managed primary runtime no longer inherits the retired router-primary `model.base_url`
- **AND** the validation proves the managed config uses `custom:ghostship-router/deepseek-v4-pro` as the primary model lane
- **AND** the validation proves the managed config uses `custom:ghostship-router/minimax-m2.7` as the fallback model lane
- **AND** the validation proves the managed config uses `firecrawl` as the web backend
- **AND** the validation proves the managed agent defaults are high reasoning and 500 max turns
