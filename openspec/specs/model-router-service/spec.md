## MODIFIED Requirements

### Requirement: Router exposes OpenCode Go model ids with explicit free equivalents
The router SHALL use OpenCode Go as the canonical served-model catalog and SHALL expose only OpenCode Go model ids that have at least one explicitly configured free-provider equivalent.

#### Scenario: Model listing exposes only mapped OpenCode Go ids
- **WHEN** a caller lists models from the router
- **THEN** the router exposes mapped OpenCode Go model ids such as `deepseek-v4-pro` and `minimax-m2.7`
- **AND** the router does not advertise OpenCode Go models without an explicit free-provider equivalence entry
- **AND** each listed model includes `free_provider_count` metadata
- **AND** each listed model includes the configured free provider names
- **AND** each listed model includes free-provider availability and RPM state

#### Scenario: Retired logical alias is rejected
- **WHEN** a caller requests a retired logical alias such as `auxiliary`, `coding`, `agentic`, `vision`, or `tts`
- **THEN** the router returns an unsupported-model style error for that alias
- **AND** the router does not silently remap the request to a different model id

### Requirement: Router routes free equivalents before same-model OpenCode Go fallback
The router SHALL route each exposed model through RPM-aware round robin across explicit free-provider equivalents first and SHALL use `opencode-go/<same OpenCode Go model id>` only as the paid fallback for that served model.

#### Scenario: Free equivalent is selected before paid fallback
- **WHEN** `deepseek-v4-pro` has configured healthy free equivalents and an OpenCode Go fallback
- **THEN** the router tries configured free equivalents with sliding-window RPM-aware round robin
- **AND** the router tries `opencode-go/deepseek-v4-pro` only after the free equivalents are unavailable or fail

#### Scenario: OpenCode Go is not counted as a free provider
- **WHEN** a model has one free equivalent and one OpenCode Go fallback
- **THEN** `/v1/models` reports `free_provider_count` as `1`
- **AND** `opencode-go` is not included in the listed free provider names

#### Scenario: OpenCode Zen remains a free provider only
- **WHEN** `opencode-zen` has an explicit equivalent for the requested OpenCode Go model id
- **THEN** the router may use `opencode-zen` as a free-provider candidate
- **AND** the router does not treat `opencode-zen` as the paid fallback catalog

### Requirement: Router provider roles are explicit
The router SHALL keep provider roles explicit so `opencode-go` is the canonical paid fallback, while NVIDIA Build, OpenCode Zen, ZenMux, Electron Hub, and explicitly mapped OpenRouter models are free-provider candidates.

#### Scenario: OpenCode Go provider is configured separately from OpenCode Zen
- **WHEN** router configuration is loaded from environment
- **THEN** `OPENCODE_GO_API_KEY` configures provider `opencode-go`
- **AND** `OPENCODE_ZEN_API_KEY` or the legacy `OPENCODE_API_KEY` configures provider `opencode-zen`
- **AND** `ZENMUX_API_KEY` configures provider `zenmux`
- **AND** `ELECTRON_HUB_API_KEY` configures provider `electron-hub`
- **AND** `opencode-go` is never classified as a free provider

#### Scenario: Free-provider RPM defaults are explicit
- **WHEN** router configuration is loaded from environment
- **THEN** `zenmux` defaults to 10 RPM
- **AND** `electron-hub` defaults to 5 RPM
- **AND** `openrouter` defaults to 20 RPM
- **AND** `nvidia-build` and `opencode-zen` default to 30 RPM

#### Scenario: Initial required models are mapped
- **WHEN** the router starts with default policy
- **THEN** `deepseek-v4-pro` has explicit free equivalent entries and `opencode-go/deepseek-v4-pro` fallback
- **AND** `minimax-m2.7` has explicit free equivalent entries and `opencode-go/minimax-m2.7` fallback
- **AND** seeded equivalents include ZenMux and Electron Hub entries for both initial served models

### Requirement: Router preserves health state and observability
The router SHALL preserve routing health state and expose enough debug information to explain provider inventory, selected candidates, and paid fallback use.

#### Scenario: Routing state survives service restart
- **WHEN** the router process stops and starts again
- **THEN** persisted inventory, health observations, cooldowns, and manual overrides remain available after restart

#### Scenario: Observability shows route candidates
- **WHEN** an operator inspects model metadata, route preview, or debug summary surfaces
- **THEN** the router exposes the ordered candidates for each served model id
- **AND** the router identifies whether a candidate is free or the OpenCode Go fallback
