## ADDED Requirements

### Requirement: Hermes runtime uses the local router as its primary OpenAI-compatible endpoint
The Hermes image SHALL configure the root Hermes runtime and the managed `operations` and `coder` profiles to use the local `ghostship-hermes-router` OpenAI-compatible API at `http://127.0.0.1:8788/v1` instead of direct upstream model endpoint defaults.

#### Scenario: Root Hermes config uses the local router
- **WHEN** the image bootstraps the root Hermes config
- **THEN** the root config sets `model.base_url` to `http://127.0.0.1:8788/v1`
- **AND** the root config sets `model.default` to `lightweight`

#### Scenario: Managed profiles use the approved router aliases
- **WHEN** the image bootstraps the managed profile configs
- **THEN** the `operations` profile sets `model.base_url` to `http://127.0.0.1:8788/v1`
- **AND** the `operations` profile sets `model.default` to `heavyweight`
- **AND** the `coder` profile sets `model.base_url` to `http://127.0.0.1:8788/v1`
- **AND** the `coder` profile sets `model.default` to `coding`

### Requirement: Managed profile gateways start behind the local router
The image SHALL treat the local router as a required dependency for the managed Hermes profile gateway services once those profiles use router aliases as their primary model identifiers.

#### Scenario: Router service starts before managed profile gateways
- **WHEN** the container boots the managed Hermes services
- **THEN** `ghostship-hermes-router.service` is started before `ghostship-hermes-profile-operations.service`
- **AND** `ghostship-hermes-router.service` is started before `ghostship-hermes-profile-coder.service`

### Requirement: Image validation proves router-primary behavior
The repo’s image validation paths SHALL verify the router-primary contract instead of only checking dashboard reachability or direct-upstream model defaults.

#### Scenario: Smoke test verifies alias discovery and configured defaults
- **WHEN** maintainers run the Hermes image dashboard smoke test
- **THEN** the test verifies `ghostship-hermes-router.service` is active
- **AND** the test verifies the router model inventory exposes `lightweight`, `coding`, and `heavyweight`
- **AND** the test verifies the root, `operations`, and `coder` configs use the approved router endpoint and alias defaults

#### Scenario: Persistence test preserves router-first config across replacement
- **WHEN** maintainers run the persistence validation through container replacement
- **THEN** the validation verifies the root, `operations`, and `coder` configs still use the approved router endpoint and alias defaults after replacement
- **AND** the validation verifies the router alias inventory remains discoverable after replacement
