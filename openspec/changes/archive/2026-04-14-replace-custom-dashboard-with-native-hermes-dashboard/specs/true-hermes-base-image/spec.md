## MODIFIED Requirements

### Requirement: Reusable base image excludes Ghostship-owned runtime surfaces
The repo SHALL build the reusable `ghostship-hermes-base` image from a base-specific image composition path that excludes Ghostship-owned runtime surfaces such as `ghostship-*`, `ghostship-hermes-router`, `ghostship-hermes-runtime`, repo-owned dashboard wrappers, `wrappedHermesAgent`, and Ghostship-managed bootstrap/tooling/profile services, while allowing the upstream Hermes runtime itself to carry its native dashboard assets and web code.

#### Scenario: Maintainer inspects the base image architecture
- **WHEN** maintainers review the flake outputs or image composition modules for `ghostship-hermes-base`
- **THEN** the base image path does not depend on shim binaries for repo-owned commands
- **AND** the base image is defined separately from the final repo-content layer
- **AND** the base/final split does not require a separate repo-owned `hermes-dashboard` package to supply the browser UI

### Requirement: Final image layers repo-owned runtime content onto the true base
The final published `ghostship-hermes` image SHALL add repo-owned router, runtime, managed-service wiring, and utility content on top of the true base image while relying on the upstream Hermes runtime/toolchain for the native dashboard browser surface.

#### Scenario: Final image is assembled from base plus repo content
- **WHEN** the final `ghostship-hermes` image is built or published
- **THEN** the real repo-owned binaries and runtime wiring are added after the base image boundary
- **AND** the final image exposes the repo-owned commands expected by operators and managed services
- **AND** the browser dashboard available in the final image comes from the upstream Hermes runtime rather than a separate repo-owned dashboard derivation
