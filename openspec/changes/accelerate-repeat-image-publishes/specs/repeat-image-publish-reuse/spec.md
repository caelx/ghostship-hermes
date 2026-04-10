## ADDED Requirements

### Requirement: Repeat image publishes reuse immutable final images first
The publish workflow SHALL derive an immutable per-architecture final-image identifier from the evaluated publish-relevant image content and SHALL check GHCR for that image before starting a rebuild.

#### Scenario: Immutable final image already exists
- **WHEN** the publish workflow evaluates the base-image and overlay-bundle derivations for an architecture and GHCR already contains the matching immutable final image
- **THEN** the workflow reuses that immutable final image instead of rebuilding it
- **AND** the workflow proceeds by retagging it into the standard architecture publish tags

#### Scenario: Immutable final image does not exist yet
- **WHEN** the publish workflow evaluates the base-image and overlay-bundle derivations for an architecture and GHCR does not contain the matching immutable final image
- **THEN** the workflow falls back to the normal build path for that architecture
- **AND** the newly built final image is published under the immutable content tag before mutable publish tags are updated

### Requirement: Repeat publish optimization stays free-only
The repeat publish optimization SHALL use existing GHCR publication and lookup capabilities as its reuse layer and SHALL NOT require a paid binary cache or external cache service.

#### Scenario: Maintainer reviews the repeat publish strategy
- **WHEN** a maintainer inspects the workflow and supporting documentation for repeat image publication
- **THEN** the documented free-only strategy uses GHCR-hosted immutable image reuse
- **AND** it does not require FlakeHub, Cachix, or another paid cache service for the repeat publish path

### Requirement: Warm-repeat publish measurements are tracked separately
The repo SHALL distinguish warm-repeat publish measurements from cold-content publish measurements when reporting the effect of the repeat-publish optimization.

#### Scenario: Maintainer reviews optimization evidence
- **WHEN** maintainers update the recorded publish timing evidence after the repeat-publish optimization lands
- **THEN** the evidence identifies whether a measurement came from a cold-content publish or a warm-repeat publish
- **AND** the warm-repeat result can be compared independently from the first-run native build path
