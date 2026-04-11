# image-publication-contract Specification

## Purpose
Define the explicit consumer contract for the low-level `ghostship-hermes-rootfs` artifact and the publishable `ghostship-hermes-image` bundle so local validation, CI publishing, and GHCR releases all consume the intended image format.
## Requirements
### Requirement: Flake image outputs have explicit consumer-specific contracts
The repo SHALL expose explicit image-related outputs so maintainers can distinguish the low-level workstation tarball artifact from the publishable `ghostship-hermes` image artifact.

#### Scenario: Maintainer inspects image outputs and docs
- **WHEN** a maintainer reads the flake outputs and repo build guidance for `ghostship-hermes`
- **THEN** the repo identifies which output is the low-level workstation tarball artifact
- **AND** the repo identifies which output is the publishable image artifact intended for GHCR and image-loading workflows

### Requirement: Publishable image artifact preserves the workstation runtime contract
The repo SHALL derive the publishable `ghostship-hermes` image artifact from the workstation runtime source artifact through a repo-owned conversion path that preserves the documented container metadata and the final managed runtime bootstrap behavior.

#### Scenario: Published image keeps expected runtime metadata
- **WHEN** maintainers build or publish the explicit publishable image artifact
- **THEN** the resulting image starts with `/init` as the runtime entry path
- **AND** the resulting image preserves the documented runtime defaults such as `HOME=/home/hermes`, `HERMES_HOME=/home/hermes/.hermes`, and port `7681`

#### Scenario: Published image keeps managed runtime bootstrap behavior
- **WHEN** maintainers publish `ghostship-hermes` to GHCR or export the explicit publishable image bundle locally
- **THEN** the resulting image preserves the final repo-owned managed runtime wiring that rewrites `/home/hermes/.hermes/.env`
- **AND** the resulting image preserves the root seed consumption behavior for `/home/hermes/.hermes/skills` and `/home/hermes/.hermes/SOUL.md`
- **AND** the published image does not silently fall back to a different upstream-only Hermes activation path

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

### Requirement: Cross-architecture validation separates evaluation from full builds
The repo SHALL distinguish arm64 derivation wiring checks from full arm64 image artifact production so x86-only maintainer and CI validation flows do not start unsupported native arm64 builds.

#### Scenario: X86 validation checks arm64 wiring without building the image
- **WHEN** a maintainer workflow or x86-only CI job validates the arm64 image path without access to an arm64-capable runner or builder
- **THEN** it evaluates the arm64 derivation path or equivalent wiring metadata
- **AND** it reserves full `aarch64-linux` image builds for an arm64-capable execution environment

### Requirement: Rootfs-oriented workstation validation consumes the low-level tarball contract
Workstation persistence validation SHALL consume the explicit low-level workstation tarball artifact rather than relying on the publishable image artifact contract.

#### Scenario: Persistence validation uses the low-level workstation artifact
- **WHEN** maintainers run the rootfs-oriented workstation persistence validation flow
- **THEN** the validation locates the explicit low-level workstation tarball artifact
- **AND** the validation does not need to guess whether `ghostship-hermes-image` refers to a rootfs tarball tree or a publishable image archive

### Requirement: Image publication runs only for image-affecting changes or explicit release triggers
GitHub Actions image publication SHALL skip automatic publish runs when a change does not affect the publishable image contract, while still allowing explicit release-triggered or manually dispatched publication.

#### Scenario: Main push changes only non-image documentation
- **WHEN** a `main` branch push changes documentation, OpenSpec archives, or other files that do not affect the publishable image contents or publication semantics
- **THEN** the automatic image publication workflow does not run
- **AND** maintainers retain an explicit manual dispatch or release-triggered path to publish the image when needed

#### Scenario: Main push changes image-affecting files
- **WHEN** a `main` branch push changes workflow, flake, package, or script content that affects the publishable image build or publication behavior
- **THEN** the automatic image publication workflow runs
- **AND** it continues to build and publish the required architecture artifacts

### Requirement: Image publication reuses supported cached build outputs
GitHub Actions image publication SHALL reuse supported cache or substituter-backed build outputs when the relevant inputs are unchanged, instead of rebuilding unchanged image dependencies from scratch on every run.

#### Scenario: Publish workflow repeats with unchanged build inputs
- **WHEN** the image publish workflow runs again with unchanged inputs for a previously built dependency or image closure
- **THEN** the workflow reuses the supported cached output where available
- **AND** the workflow still produces the same explicit publishable image contract

### Requirement: Image publication may use a faster internal assembly architecture while preserving the external contract
The repo SHALL permit internal build and publication architecture changes that materially reduce wall-clock time, provided the resulting published image remains compatible with the explicit `ghostship-hermes-image` contract.

#### Scenario: Faster publication architecture is introduced
- **WHEN** maintainers replace part of the internal image assembly or publication flow with a materially faster architecture
- **THEN** the published image still preserves the documented runtime metadata and multi-arch release semantics
- **AND** downstream consumers do not need to change how they consume the explicit publishable image artifact

