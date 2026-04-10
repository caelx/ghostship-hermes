# google-cloud-cli-runtime Specification

## Purpose

Define the default-image contract for shipping the Google Cloud CLI in the Hermes runtime through the repo's normal Nix/image package wiring.

## Requirements

### Requirement: Hermes image ships the Google Cloud CLI
The default Hermes image SHALL include the `gcloud` executable on `PATH`, and the executable SHALL come from the repo's normal Nix/image package wiring rather than an ad hoc runtime installer.

#### Scenario: Default image exposes `gcloud`
- **WHEN** the default Hermes image is built from the repo flake
- **THEN** the image contents include the `gcloud` executable
- **AND** the executable is available on `PATH` inside the container runtime without an additional installation step

### Requirement: Repo evaluation covers the Google Cloud CLI package
The repo flake SHALL evaluate the Google Cloud CLI integration as part of normal package and image wiring so integration failures appear during standard flake checks, derivation inspection, or image build workflows.

#### Scenario: Flake evaluation includes the Google Cloud CLI package
- **WHEN** maintainers run the repo's flake checks or inspect package outputs
- **THEN** the Google Cloud CLI package wiring evaluates successfully as part of the repo flake outputs
- **AND** the default Hermes image package depends on that evaluated package path

### Requirement: Runtime policy documents the Google Cloud CLI as an approved extra tool
The repo's runtime policy and operator guidance SHALL describe `gcloud` as an approved non-`ghostship-*` CLI in the default image.

#### Scenario: Approved extra-CLI policy includes `gcloud`
- **WHEN** maintainers inspect the runtime policy and image guidance
- **THEN** the documented approved non-`ghostship-*` CLI set includes `gcloud`
- **AND** that documentation aligns with the image package wiring that exposes the executable on `PATH`
