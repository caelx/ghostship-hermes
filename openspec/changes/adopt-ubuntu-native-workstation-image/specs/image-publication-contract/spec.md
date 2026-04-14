## ADDED Requirements

### Requirement: GitHub Actions publishes the Ubuntu workstation image contract
The repository SHALL build, validate, and publish the Ubuntu 24.04 workstation image as the supported `ghostship-hermes` publication artifact.

#### Scenario: Publish workflow builds the workstation image
- **WHEN** the repository runs its image publication workflow for a publishable ref
- **THEN** the workflow builds the Ubuntu 24.04 workstation image
- **AND** the published artifact reflects the runtime contract with `/opt/hermes`, `s6`, the mandatory router, the upstream dashboard plus console patch, and the documented persistence layout

### Requirement: Publication validates the actual final workstation image
The publication workflow SHALL validate the exact final workstation image before publication rather than relying only on checks for a different build artifact or an older NixOS image path.

#### Scenario: Final image validation runs before publication
- **WHEN** the repository prepares to publish a workstation image
- **THEN** the workflow runs validation against the actual final image artifact that will be published
- **AND** that validation covers the supported runtime, browser, supervision, and persistence assumptions for the workstation image

### Requirement: Publication docs stay aligned with the image contract
The repository SHALL keep the published deployment guidance aligned with the actual image being built and published.

#### Scenario: Operator reads the published image guidance
- **WHEN** a downstream operator reads the documented deployment examples for the published image
- **THEN** the examples match the current workstation image contract for mounts, environment variables, browser port, and service behavior
- **AND** the docs do not describe the retired NixOS/module-managed runtime as the supported image
