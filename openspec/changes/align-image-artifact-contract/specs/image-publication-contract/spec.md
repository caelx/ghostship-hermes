## ADDED Requirements

### Requirement: Flake image outputs have explicit consumer-specific contracts
The repo SHALL expose explicit image-related outputs so maintainers can distinguish the low-level workstation tarball artifact from the publishable `ghostship-hermes` image artifact.

#### Scenario: Maintainer inspects image outputs and docs
- **WHEN** a maintainer reads the flake outputs and repo build guidance for `ghostship-hermes`
- **THEN** the repo identifies which output is the low-level workstation tarball artifact
- **AND** the repo identifies which output is the publishable image artifact intended for GHCR and image-loading workflows

### Requirement: Publishable image artifact preserves the workstation runtime contract
The repo SHALL derive the publishable `ghostship-hermes` image artifact from the workstation runtime source artifact through a repo-owned conversion path that preserves the documented container metadata.

#### Scenario: Published image keeps expected runtime metadata
- **WHEN** maintainers build or publish the explicit publishable image artifact
- **THEN** the resulting image starts with `/init` as the runtime entry path
- **AND** the resulting image preserves the documented workstation defaults such as `HOME=/home/hermes`, `HERMES_HOME=/opt/data`, and port `7681`

### Requirement: CI and image tests consume the publishable image contract
GitHub Actions image publication and image-focused test helpers SHALL consume the explicit publishable image artifact instead of inferring image semantics from the low-level workstation tarball layout.

#### Scenario: Image publishing uses the explicit publishable artifact
- **WHEN** the GitHub image publish workflow builds and uploads architecture-specific artifacts
- **THEN** it uses the explicit publishable image artifact contract
- **AND** it does not assume that the flake result path is directly a single `docker-archive` file unless that is the declared publishable artifact format

#### Scenario: Image smoke tests use the explicit publishable artifact
- **WHEN** maintainers run repo image-focused tests that load or start `ghostship-hermes`
- **THEN** those tests consume the explicit publishable image artifact contract
- **AND** they do not depend on a stale archive format that differs from CI publishing

### Requirement: Rootfs-oriented workstation validation consumes the low-level tarball contract
Workstation persistence validation SHALL consume the explicit low-level workstation tarball artifact rather than relying on the publishable image artifact contract.

#### Scenario: Persistence validation uses the low-level workstation artifact
- **WHEN** maintainers run the rootfs-oriented workstation persistence validation flow
- **THEN** the validation locates the explicit low-level workstation tarball artifact
- **AND** the validation does not need to guess whether `ghostship-hermes-image` refers to a rootfs tarball tree or a publishable image archive
