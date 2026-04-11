## MODIFIED Requirements

### Requirement: Image publication may use a faster internal assembly architecture while preserving the external contract
The repo SHALL permit internal build and publication architecture changes that materially reduce wall-clock time, provided the resulting published image remains compatible with the explicit `ghostship-hermes-image` contract.

#### Scenario: Faster publication architecture is introduced
- **WHEN** maintainers replace part of the internal image assembly or publication flow with a materially faster architecture
- **THEN** the published image still preserves the documented runtime metadata and multi-arch release semantics
- **AND** downstream consumers do not need to change how they consume the explicit publishable image artifact

#### Scenario: GitHub fast path verifies the publish-bound image
- **WHEN** the GitHub publish workflow uses an internal assembly path other than exporting the explicit `ghostship-hermes-image` bundle directly
- **THEN** the workflow verifies the exact image it is about to publish against the managed runtime bootstrap contract
- **AND** the workflow does not treat a different local-only artifact path as sufficient proof that the publish-bound image matches the explicit contract
