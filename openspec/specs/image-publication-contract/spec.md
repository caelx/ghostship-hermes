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

#### Scenario: Publish workflow consumes the shared Ghostship cache
- **WHEN** `publish-image` is configured to use `caelx/ghostship-cache`
- **THEN** the workflow consumes cached Nix store paths through the supported shared-cache proxy/substituter path
- **AND** it still builds the explicit `ghostship-hermes-image` bundle on the runner host before export/publication

#### Scenario: Shared-cache miss falls back to the normal publish path
- **WHEN** the shared Ghostship cache is empty or unavailable before the publish build starts
- **THEN** `publish-image` continues with the normal full host-side build path
- **AND** it does not switch to a different image assembly architecture or publish a different artifact contract

### Requirement: Image publication may use a faster internal assembly architecture while preserving the external contract
The repo SHALL permit internal build and publication architecture changes that materially reduce wall-clock time, provided the resulting published image remains compatible with the explicit `ghostship-hermes-image` contract.

#### Scenario: Faster publication architecture is introduced
- **WHEN** maintainers replace part of the internal image assembly or publication flow with a materially faster architecture
- **THEN** the published image still preserves the documented runtime metadata and multi-arch release semantics
- **AND** downstream consumers do not need to change how they consume the explicit publishable image artifact

#### Scenario: GitHub fast path uses layered assembly internally
- **WHEN** the GitHub publish workflow publishes architecture images from the reusable `ghostship-hermes-base` tag plus `ghostship-hermes-overlay-bundle`
- **THEN** the workflow still preserves the documented runtime metadata and multi-arch release semantics of the published image
- **AND** local export and smoke-test flows continue to use the explicit `ghostship-hermes-image` bundle instead of guessing from the GitHub layering internals

### Requirement: Cache upload planning happens before the real publish build when using a dry-run planner
If `publish-image` uses a cache planner that identifies upload candidates from `nix build --dry-run`, the workflow SHALL run that planning step before the real image build and carry the resulting plan forward to later cache publication.

#### Scenario: Cold run prepares upload candidates before build
- **WHEN** `publish-image` is about to build `ghostship-hermes-image` on a runner without a usable shared-cache index
- **THEN** the workflow computes the shared-cache upload plan before the real `nix build` starts
- **AND** the later cache publication step uses that saved plan instead of recomputing candidates after the build

### Requirement: Cache planning failure does not block image publication
`publish-image` SHALL continue to publish the explicit `ghostship-hermes-image` artifact even when shared-cache planning fails before the build starts.

#### Scenario: Pre-build cache planning fails
- **WHEN** the pre-build shared-cache planning step errors or times out
- **THEN** the workflow continues with the normal host-side image build and publication path
- **AND** it skips only the affected cache publication leg rather than failing image publication

### Requirement: Warm-cache reuse is observable in workflow evidence
The image publication workflow or its runbook SHALL provide maintainers enough evidence to tell whether a repeat publish consumed the shared cache, rather than relying only on final duration comparisons.

#### Scenario: Maintainer inspects a repeat publish run
- **WHEN** a maintainer reviews a repeat `publish-image` run after a successful cache seed
- **THEN** the run exposes whether shared-cache bootstrap succeeded before `nix build`
- **AND** the run provides log evidence that cached store paths were reused or that the build fell back to uncached behavior

