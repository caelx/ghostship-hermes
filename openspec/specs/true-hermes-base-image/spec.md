## MODIFIED Requirements

### Requirement: Reusable base image excludes Ghostship-owned runtime surfaces
The repo SHALL build any reusable base image from an Ubuntu 24.04 composition that includes Hermes core, baked-in Nix, and only the minimum shared runtime dependencies, while excluding Ghostship-owned router, dashboard-extension, and other repo-specific runtime surfaces from that base layer.

#### Scenario: Maintainer inspects the base image architecture
- **WHEN** maintainers review the workstation image architecture or any reusable base artifact derived from it
- **THEN** the base layer contains the Ubuntu base OS, image-owned Hermes core, Nix, and shared runtime prerequisites
- **AND** the base layer excludes the Ghostship router, the dashboard console patch layer, and other repo-owned product-specific wiring

### Requirement: Base image keeps only Hermes and core container boot responsibilities
The reusable base image SHALL keep only the upstream Hermes runtime and the core container boot/runtime contract required before repo-owned content is layered in.

#### Scenario: Base image is composed
- **WHEN** the reusable base image is built
- **THEN** it preserves the container boot essentials needed to reach the final workstation runtime contract
- **AND** it does not include repo-owned router, console-tab dashboard patch, or other final-image-only service wiring

### Requirement: Final image layers repo-owned runtime content onto the true base
The final published `ghostship-hermes` image SHALL add the repo-owned router, dashboard console extension, runtime wiring, and any remaining approved product-specific content on top of the Ubuntu/Hermes/Nix base layer.

#### Scenario: Final image is assembled from base plus repo content
- **WHEN** the final `ghostship-hermes` image is built or published
- **THEN** the repo-owned router, dashboard console extension, and final runtime wiring are added after the base image boundary
- **AND** the final image exposes the repo-owned commands and services expected by operators
