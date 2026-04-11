## MODIFIED Requirements

### Requirement: Publishable image artifact preserves the workstation runtime contract
The repo SHALL derive the publishable `ghostship-hermes` image artifact from the workstation runtime source artifact through a repo-owned conversion or layered-image assembly path that preserves the documented container metadata.

#### Scenario: Published image keeps expected runtime metadata
- **WHEN** maintainers build, assemble, or publish the explicit publishable image artifact
- **THEN** the resulting image starts with `/init` as the runtime entry path
- **AND** the resulting image preserves the documented runtime defaults such as `HOME=/home/hermes`, `HERMES_HOME=/home/hermes/.hermes`, and port `7681`

### Requirement: CI and image tests consume the publishable image contract
GitHub Actions image publication and image-focused test helpers SHALL consume the explicit publishable image artifact instead of inferring image semantics from the low-level workstation tarball layout. Architecture-specific publication builds SHALL run on a runner or builder environment that can execute the target system's Nix derivations, and x86-only validation paths MUST limit arm64 checks to derivation evaluation unless an executable arm64 builder is configured. Internal publication MAY assemble the final image by layering repo-owned content onto a reusable base image, provided the resulting publishable image artifact still matches the documented consumer contract.

#### Scenario: Image publishing uses the explicit publishable artifact
- **WHEN** the GitHub image publish workflow builds, assembles, or uploads architecture-specific artifacts
- **THEN** it uses the explicit publishable image artifact contract
- **AND** it does not assume that the flake result path is directly a single `docker-archive` file unless that is the declared publishable artifact format
- **AND** each architecture build runs on infrastructure that can execute that architecture's Nix derivations

#### Scenario: Arm64 image publication uses an executable arm64 build environment
- **WHEN** the GitHub image publish workflow builds the `aarch64-linux` publishable image artifact
- **THEN** the job runs on an arm64-capable runner or a configured builder that can execute `aarch64-linux` derivations
- **AND** the workflow does not rely on Docker QEMU or Nix `extra-platforms` alone to satisfy the native arm64 build requirement

#### Scenario: Final image is assembled from a reusable base layer
- **WHEN** the GitHub image publish workflow uses a reusable base image plus repo-owned final content to produce `ghostship-hermes`
- **THEN** downstream consumers still receive the same `ghostship-hermes` mutable tags and manifest-list semantics
- **AND** the final image continues to satisfy the documented runtime contract

#### Scenario: Image smoke tests use the explicit publishable artifact
- **WHEN** maintainers run repo image-focused tests that load or start `ghostship-hermes`
- **THEN** those tests consume the explicit publishable image artifact contract
- **AND** they do not depend on a stale archive format that differs from CI publishing
