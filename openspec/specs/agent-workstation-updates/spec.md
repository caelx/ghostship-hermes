## MODIFIED Requirements

### Requirement: Supported doctor warnings are reduced through the managed runtime layers
The workstation SHALL wire the runtime dependencies, managed-state markers, and shared env needed for Hermes operator health reporting so the checks that correspond to intentionally supported features reflect the real managed runtime state.

#### Scenario: Doctor reflects supported features
- **WHEN** the operator runs `hermes -p <profile> doctor`
- **THEN** the managed runtime reduces avoidable warnings for the supported Hermes, Codex, browser, GitHub-token, Home Assistant, and supported profile-facing env projection paths
- **AND** supported profile-facing integrations do not warn only because bootstrap failed to project documented runtime env into the managed profile `.env`
- **AND** healthy managed profile gateways do not appear stopped solely because upstream gateway service discovery does not match the repo-owned unit names
- **AND** intentionally unsupported optional integrations may still report warnings

## ADDED Requirements

### Requirement: Managed gateway health reporting matches runtime truth
The workstation SHALL keep operator-facing gateway health output aligned with the actual managed profile runtime.

#### Scenario: Healthy managed profile gateways are reported as running
- **WHEN** the managed profile gateway service is active and its profile state is healthy enough for normal operation
- **THEN** operator-facing health output reports that profile gateway as running
- **AND** status output does not regress to a false stopped state because the runtime is Nix-managed

#### Scenario: Managed runtime guidance replaces upstream recovery instructions
- **WHEN** the operator asks Hermes for managed gateway status or recovery guidance inside the image
- **THEN** the guidance references the repo-managed runtime contract
- **AND** it does not recommend upstream user-service recovery steps that are incompatible with the image's managed systemd topology
