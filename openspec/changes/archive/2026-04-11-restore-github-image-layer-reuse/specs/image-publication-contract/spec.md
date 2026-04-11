## MODIFIED Requirements

### Requirement: Image publication may use a faster internal assembly architecture while preserving the external contract
The repo SHALL permit internal build and publication architecture changes that materially reduce wall-clock time, provided the resulting published image remains compatible with the explicit `ghostship-hermes-image` contract.

#### Scenario: Faster publication architecture is introduced
- **WHEN** maintainers replace part of the internal image assembly or publication flow with a materially faster architecture
- **THEN** the published image still preserves the documented runtime metadata and multi-arch release semantics
- **AND** downstream consumers do not need to change how they consume the explicit publishable image artifact

#### Scenario: GitHub fast path uses layered assembly internally
- **WHEN** the GitHub publish workflow publishes architecture images from the reusable `ghostship-hermes-base` tag plus `ghostship-hermes-overlay-bundle`
- **THEN** the workflow still preserves the documented runtime metadata and multi-arch release semantics of the published image
- **AND** local export and smoke-test flows continue to use the explicit `ghostship-hermes-image` bundle instead of guessing from the GitHub layering internals
