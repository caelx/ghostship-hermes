## MODIFIED Requirements

### Requirement: Hermes runtime uses the local router as its primary OpenAI-compatible endpoint
The Hermes image SHALL configure the managed Hermes runtime to use the local `ghostship-hermes-router` OpenAI-compatible API at `http://127.0.0.1:8788/v1` instead of direct upstream model endpoint defaults.

#### Scenario: Managed Hermes config uses the local router
- **WHEN** the image bootstraps the managed Hermes config
- **THEN** the managed config sets `model.provider` to `auto`
- **AND** the managed config sets `model.base_url` to `http://127.0.0.1:8788/v1`
- **AND** the managed config sets `model.default` to `coding`

### Requirement: Managed gateway starts behind the local router
The image SHALL treat the local router as a required dependency for the managed Hermes gateway service once the managed runtime uses router aliases as its primary model identifiers.

#### Scenario: Router service starts before the managed gateway
- **WHEN** the container boots the managed Hermes services
- **THEN** `ghostship-hermes-router.service` is started before `ghostship-hermes-gateway.service`

### Requirement: Image validation proves router-primary behavior
The repo's image validation paths SHALL verify the router-primary contract instead of only checking dashboard reachability or direct-upstream model defaults.

#### Scenario: Smoke test verifies alias discovery and configured defaults
- **WHEN** maintainers run the Hermes image dashboard smoke test
- **THEN** the test verifies `ghostship-hermes-router.service` is active
- **AND** the test verifies the router model inventory exposes `auxiliary`, `coding`, `agentic`, `vision`, and `tts`
- **AND** the test verifies the managed Hermes config uses `provider = auto`, `base_url = http://127.0.0.1:8788/v1`, and `default = coding`

#### Scenario: Persistence test preserves router-first config across replacement
- **WHEN** maintainers run the persistence validation through container replacement
- **THEN** the validation verifies the managed Hermes config still uses `provider = auto`, `base_url = http://127.0.0.1:8788/v1`, and `default = coding` after replacement
- **AND** the validation verifies the router alias inventory remains discoverable after replacement
