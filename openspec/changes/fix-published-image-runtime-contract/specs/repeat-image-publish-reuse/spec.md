## MODIFIED Requirements

### Requirement: Repeat image publishes reuse immutable final images first
The publish workflow SHALL derive an immutable per-architecture final-image identifier from the explicit publishable image artifact or its direct Nix source derivation and SHALL check GHCR for that image before starting a rebuild.

#### Scenario: Immutable final image already exists
- **WHEN** the publish workflow evaluates the explicit publishable `ghostship-hermes-image` artifact for an architecture and GHCR already contains the matching immutable final image
- **THEN** the workflow reuses that immutable final image instead of rebuilding it
- **AND** the workflow proceeds by retagging it into the standard architecture publish tags

#### Scenario: Immutable final image does not exist yet
- **WHEN** the publish workflow evaluates the explicit publishable `ghostship-hermes-image` artifact for an architecture and GHCR does not contain the matching immutable final image
- **THEN** the workflow falls back to the normal build-and-export path for that architecture
- **AND** the newly built final image is published under the immutable content tag before mutable publish tags are updated
