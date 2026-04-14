## ADDED Requirements

### Requirement: Managed runtime removes unsupported Discord plugin steering
The workstation SHALL remove unsupported repo-owned Discord plugin steering paths from the managed Hermes runtime so Discord model routing behavior is owned only by the supported wrapper guard.

#### Scenario: Managed runtime no longer depends on the old Discord plugin path
- **WHEN** maintainers inspect the repo-owned Hermes runtime behavior for Discord model selection
- **THEN** the managed runtime does not depend on a legacy repo-owned Discord plugin path to steer free-response model routing
- **AND** the supported behavior is the wrapper-enforced Discord free-channel router pin instead
