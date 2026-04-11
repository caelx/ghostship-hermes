# true-hermes-base-image Specification

## Purpose
TBD - created by archiving change optimize-github-actions-image-builds. Update Purpose after archive.
## Requirements
### Requirement: Reusable base image excludes Ghostship-owned runtime surfaces
The repo SHALL build the reusable `ghostship-hermes-base` image from a base-specific image composition path that excludes Ghostship-owned runtime surfaces such as `ghostship-*`, `ghostship-hermes-router`, `ghostship-hermes-runtime`, `hermes-dashboard`, `wrappedHermesAgent`, and Ghostship-managed bootstrap/tooling/profile services.

#### Scenario: Maintainer inspects the base image architecture
- **WHEN** maintainers review the flake outputs or image composition modules for `ghostship-hermes-base`
- **THEN** the base image path does not depend on shim binaries for repo-owned commands
- **AND** the base image is defined separately from the final repo-content layer

### Requirement: Base image keeps only Hermes and core container boot responsibilities
The reusable `ghostship-hermes-base` image SHALL keep the upstream Hermes runtime and the core container boot/runtime contract required before repo-owned content is layered in.

#### Scenario: Base image is composed
- **WHEN** the reusable base image is built
- **THEN** it preserves the container boot essentials needed to reach the final runtime contract
- **AND** it does not include repo-owned router, dashboard, or utility wiring that belongs only to the final image

### Requirement: Base image may include stable shared dependency closures
The reusable `ghostship-hermes-base` image SHALL include stable shared runtimes or dependency closures when they materially reduce the amount of repo-owned content that must be layered in later, provided those dependencies do not themselves introduce repo-owned service wiring.

#### Scenario: Maintainer chooses dependencies for the base layer
- **WHEN** maintainers decide whether a shared dependency belongs in the base image
- **THEN** they include it only if it is broadly reused and sufficiently stable across repo-owned final content
- **AND** they do not use that dependency choice to smuggle repo-owned command surfaces back into the base layer

### Requirement: Final image layers repo-owned runtime content onto the true base
The final published `ghostship-hermes` image SHALL add repo-owned router, dashboard, runtime, and utility content on top of the true base image rather than requiring those command surfaces inside the base closure.

#### Scenario: Final image is assembled from base plus repo content
- **WHEN** the final `ghostship-hermes` image is built or published
- **THEN** the real repo-owned binaries and runtime wiring are added after the base image boundary
- **AND** the final image exposes the repo-owned commands expected by operators and managed services

### Requirement: Base-image verification inspects the built closure
The repo SHALL verify the true-base split against the built `ghostship-hermes-base` closure or realized image contents, not only against source-level module boundaries.

#### Scenario: Maintainer validates the base image
- **WHEN** maintainers validate the true-base split
- **THEN** they inspect the built base derivation, its realized closure, or both
- **AND** they confirm Ghostship-owned runtime packages are absent while approved shared dependencies remain present

