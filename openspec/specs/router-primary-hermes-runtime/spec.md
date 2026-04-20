## ADDED Requirements

### Requirement: Hermes runtime uses Codex as its primary model path
The Hermes image SHALL configure the managed Hermes runtime to use `openai-codex/gpt-5.4` as the primary model lane, SHALL keep direct `opencode-go/minimax-m2.7` as the configured fallback model lane, and SHALL expose the local `ghostship-hermes-router` OpenAI-compatible API as a managed custom provider pinned to alias `agentic`.

#### Scenario: Managed Hermes config uses Codex primary, OpenCode fallback, and router custom provider
- **WHEN** the image bootstraps the managed Hermes config
- **THEN** the managed config sets `model.provider` to `openai-codex`
- **AND** the managed config sets `model.default` to `gpt-5.4`
- **AND** the managed config does not leave a router-primary `model.base_url` in place for the direct primary lane
- **AND** the managed config sets `fallback_model.provider` to `opencode-go`
- **AND** the managed config sets `fallback_model.model` to `minimax-m2.7`
- **AND** the managed config does not leave retired router fallback fields such as `fallback_model.base_url = http://127.0.0.1:8788/v1`
- **AND** the managed config contains a `custom_providers` entry named `ghostship-router`
- **AND** that `custom_providers` entry sets `base_url` to `http://127.0.0.1:8788/v1`
- **AND** that `custom_providers` entry sets `api_key_env` to `_GHOSTSHIP_ROUTER_API_KEY`
- **AND** that `custom_providers` entry sets `model` to `agentic`

### Requirement: Managed config convergence removes retired router-primary drift
The image SHALL reconcile repo-owned managed config on boot so stale managed provider-order fields from older image generations do not continue shadowing the current Codex-primary contract.

#### Scenario: Persisted retired provider order is rewritten during managed convergence
- **WHEN** the container boots with persisted `/home/hermes/.hermes/config.yaml` from an older router-primary image generation
- **THEN** managed convergence removes any retired root-managed `model.base_url` value that points at `http://127.0.0.1:8788/v1`
- **AND** managed convergence rewrites the managed primary model contract to `openai-codex/gpt-5.4`
- **AND** managed convergence rewrites the managed fallback model contract to `opencode-go/minimax-m2.7`
- **AND** managed convergence sets the managed `agent.reasoning_effort` default to `medium`

### Requirement: Image validation proves direct-primary behavior
The repo's image validation paths SHALL verify the Codex-primary contract instead of accepting successful fallback-rescued replies or stale config text as proof that the managed model order is correct.

#### Scenario: Validation proves the runtime no longer uses the retired provider order
- **WHEN** maintainers run the Hermes image validation suite
- **THEN** the validation proves the managed primary runtime no longer inherits the retired router-primary `model.base_url`
- **AND** the validation proves the managed config uses `openai-codex/gpt-5.4` as the primary model lane
- **AND** the validation proves the managed config uses `opencode-go/minimax-m2.7` as the fallback model lane
- **AND** the validation proves the managed `ghostship-router` custom provider remains pinned to `agentic`
- **AND** the validation does not treat stale fallback wiring, stale config text, or removed Discord env references as acceptable proof of the new contract

### Requirement: Managed agent defaults match the Codex primary lane
The Hermes image SHALL set the repo-owned managed agent defaults so the primary Codex lane uses the intended default thinking level.

#### Scenario: Managed config seeds medium reasoning effort
- **WHEN** the image bootstraps the managed Hermes config
- **THEN** the managed config sets `agent.reasoning_effort` to `medium`
- **AND** the managed runtime does not keep the retired managed default of `high`
