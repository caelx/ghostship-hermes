## REMOVED Requirements

### Requirement: Hermes runtime uses the local router as its primary OpenAI-compatible endpoint
**Reason**: The old requirement encoded a root-plus-profile topology that no longer exists in the supported runtime.
**Migration**: Apply the router-primary contract, when enabled, to the single managed agent instead of root plus named profiles.

### Requirement: Managed profile gateways start behind the local router
**Reason**: The runtime no longer supervises multiple profile gateway services.
**Migration**: Order the router ahead of the single managed gateway service.

### Requirement: Image validation proves router-primary behavior
**Reason**: Validation still matters, but it now targets one managed agent config and one managed gateway service.
**Migration**: Rewrite smoke and persistence tests to assert router-primary behavior for the single managed agent.

## ADDED Requirements

### Requirement: The single managed agent uses the local router when the image is configured for router-primary operation
The Hermes image SHALL configure the single managed agent to use the local `ghostship-hermes-router` OpenAI-compatible API at `http://127.0.0.1:8788/v1` when the image is operating in its router-primary mode.

#### Scenario: Managed agent config uses the local router
- **WHEN** the image bootstraps the managed single-agent config in router-primary mode
- **THEN** the managed config sets `model.base_url` to `http://127.0.0.1:8788/v1`
- **AND** the managed config sets `model.default` to the repo-approved router alias for the single-agent runtime

### Requirement: The managed gateway starts behind the local router
The image SHALL treat the local router as a required dependency for the managed Hermes gateway service when the managed runtime uses router aliases as its primary model identifiers.

#### Scenario: Router service starts before the managed gateway
- **WHEN** the container boots the managed Hermes services in router-primary mode
- **THEN** `ghostship-hermes-router.service` is started before the repo-owned managed gateway service

### Requirement: Image validation proves single-agent router-primary behavior
The repo’s image validation paths SHALL verify the router-primary contract for the single managed agent instead of only checking dashboard reachability or named-profile defaults.

#### Scenario: Smoke test verifies alias discovery and configured defaults
- **WHEN** maintainers run the Hermes image dashboard smoke test in router-primary mode
- **THEN** the test verifies `ghostship-hermes-router.service` is active
- **AND** the test verifies the router model inventory exposes the repo-approved alias set
- **AND** the test verifies the managed single-agent config uses the approved router endpoint and alias default

#### Scenario: Persistence test preserves router-first config across replacement
- **WHEN** maintainers run the persistence validation through container replacement in router-primary mode
- **THEN** the validation verifies the managed single-agent config still uses the approved router endpoint and alias default after replacement
- **AND** the validation verifies the router alias inventory remains discoverable after replacement
