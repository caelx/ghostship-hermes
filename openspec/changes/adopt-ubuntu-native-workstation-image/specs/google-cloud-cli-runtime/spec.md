## MODIFIED Requirements

### Requirement: Hermes image ships the Google Cloud CLI
The workstation contract SHALL document `gcloud` as an optional userland tool rather than as a default seeded image tool, while still giving downstream a supported persisted install path for it.

#### Scenario: Docs describe how optional `gcloud` persists
- **WHEN** maintainers inspect the runtime docs
- **THEN** the docs explain how downstream can install `gcloud` through a supported persisted userland path
- **AND** the docs do not claim `gcloud` is preinstalled by default

### Requirement: Runtime policy documents the Google Cloud CLI as an approved extra tool
The repo's runtime policy and operator guidance SHALL describe `gcloud` as an approved optional workstation tool while distinguishing it from the smaller immutable core image tool set.

#### Scenario: Approved extra-CLI policy includes `gcloud` in the optional userland layer
- **WHEN** maintainers inspect the runtime policy and image guidance
- **THEN** the documented approved optional workstation tool set includes `gcloud`
- **AND** that documentation distinguishes optional userland installation from the immutable core image layer
