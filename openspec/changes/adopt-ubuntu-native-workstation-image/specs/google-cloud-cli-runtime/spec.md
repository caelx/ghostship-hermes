## MODIFIED Requirements

### Requirement: Hermes image ships the Google Cloud CLI
The default workstation contract SHALL make `gcloud` available on `PATH` through the repo’s default persisted userland Nix layer rather than requiring the executable to live in the immutable core image.

#### Scenario: Default workstation exposes `gcloud`
- **WHEN** the workstation has completed its supported default userland Nix initialization
- **THEN** the runtime exposes the `gcloud` executable
- **AND** the executable is available on `PATH` inside the container runtime without an additional manual installation step

### Requirement: Runtime policy documents the Google Cloud CLI as an approved extra tool
The repo's runtime policy and operator guidance SHALL describe `gcloud` as an approved default workstation tool while distinguishing it from the smaller immutable core image tool set.

#### Scenario: Approved extra-CLI policy includes `gcloud` in the default userland layer
- **WHEN** maintainers inspect the runtime policy and image guidance
- **THEN** the documented approved default workstation tool set includes `gcloud`
- **AND** that documentation distinguishes the default userland layer from the immutable core image layer
