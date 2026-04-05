## MODIFIED Requirements

### Requirement: CI and image tests consume the publishable image contract
GitHub Actions image publication and image-focused test helpers SHALL consume the explicit publishable image artifact instead of inferring image semantics from the low-level workstation tarball layout. Architecture-specific publication builds SHALL run on a runner or builder environment that can execute the target system's Nix derivations, and x86-only validation paths MUST limit arm64 checks to derivation evaluation unless an executable arm64 builder is configured.

#### Scenario: Image publishing uses the explicit publishable artifact
- **WHEN** the GitHub image publish workflow builds and uploads architecture-specific artifacts
- **THEN** it uses the explicit publishable image artifact contract
- **AND** it does not assume that the flake result path is directly a single `docker-archive` file unless that is the declared publishable artifact format
- **AND** each architecture build runs on infrastructure that can execute that architecture's Nix derivations

#### Scenario: Arm64 image publication uses an executable arm64 build environment
- **WHEN** the GitHub image publish workflow builds the `aarch64-linux` publishable image artifact
- **THEN** the job runs on an arm64-capable runner or a configured builder that can execute `aarch64-linux` derivations
- **AND** the workflow does not rely on Docker QEMU or Nix `extra-platforms` alone to satisfy the native arm64 build requirement

#### Scenario: Image smoke tests use the explicit publishable artifact
- **WHEN** maintainers run repo image-focused tests that load or start `ghostship-hermes`
- **THEN** those tests consume the explicit publishable image artifact contract
- **AND** they do not depend on a stale archive format that differs from CI publishing

## ADDED Requirements

### Requirement: Cross-architecture validation separates evaluation from full builds
The repo SHALL distinguish arm64 derivation wiring checks from full arm64 image artifact production so x86-only maintainer and CI validation flows do not start unsupported native arm64 builds.

#### Scenario: X86 validation checks arm64 wiring without building the image
- **WHEN** a maintainer workflow or x86-only CI job validates the arm64 image path without access to an arm64-capable runner or builder
- **THEN** it evaluates the arm64 derivation path or equivalent wiring metadata
- **AND** it reserves full `aarch64-linux` image builds for an arm64-capable execution environment
