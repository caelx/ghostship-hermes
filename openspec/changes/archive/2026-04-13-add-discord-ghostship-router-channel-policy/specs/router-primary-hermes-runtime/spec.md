## MODIFIED Requirements

### Requirement: Hermes runtime uses direct OpenCode Go as its primary model path
The Hermes image SHALL configure the managed Hermes runtime to use direct `opencode-go/minimax-m2.7` as the primary model lane, SHALL use `openai-codex/gpt-5.4-mini` as the configured fallback lane, and SHALL expose the local `ghostship-hermes-router` OpenAI-compatible API as a named manual custom provider instead of the configured fallback model.

#### Scenario: Managed Hermes config uses direct primary, Codex fallback, and named router provider
- **WHEN** the image bootstraps the managed Hermes config
- **THEN** the managed config sets `model.provider` to `opencode-go`
- **AND** the managed config sets `model.default` to `minimax-m2.7`
- **AND** the managed config does not leave a router-primary `model.base_url` in place for the direct primary lane
- **AND** the managed config sets `fallback_model.provider` to `openai-codex`
- **AND** the managed config sets `fallback_model.model` to `gpt-5.4-mini`
- **AND** the managed config defines one named custom provider `ghostship-router`
- **AND** that custom provider points at `http://127.0.0.1:8788/v1`

#### Scenario: Manual router provider exposes live router models
- **WHEN** an operator or Discord user targets the named custom provider `ghostship-router`
- **THEN** Hermes uses the router endpoint's live `/models` inventory to resolve available model ids
- **AND** the runtime does not require one custom provider entry per router-exposed model id
