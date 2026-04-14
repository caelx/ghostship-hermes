## MODIFIED Requirements

### Requirement: Hermes image ships the Google Cloud CLI
The workstation contract SHALL document `gcloud` as part of the baseline image-managed helper set delivered through the reconciled managed Nix default profile.

#### Scenario: Docs describe the shipped `gcloud` runtime path
- **WHEN** maintainers inspect the runtime docs
- **THEN** the docs state that `gcloud` is part of the baseline image-managed helper set
- **AND** the docs describe that `gcloud` resolves through the managed Nix default profile that is reconciled into persisted `/nix`
- **AND** the docs do not describe `gcloud` as a downstream-only manual install
