## ADDED Requirements

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
