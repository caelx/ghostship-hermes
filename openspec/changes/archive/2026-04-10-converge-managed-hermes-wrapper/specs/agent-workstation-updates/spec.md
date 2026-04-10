## MODIFIED Requirements

### Requirement: Supported doctor warnings are reduced through the managed runtime layers
The workstation SHALL wire the runtime dependencies, managed-state markers, and shared env needed for Hermes operator health reporting so the checks that correspond to intentionally supported features reflect the real managed runtime state.

#### Scenario: Doctor reflects supported features
- **WHEN** the operator runs `hermes -p <profile> doctor`
- **THEN** the managed runtime reduces avoidable warnings for the supported Hermes, Codex, browser, GitHub-token, Home Assistant, and supported profile-facing env projection paths
- **AND** supported profile-facing integrations do not warn only because bootstrap failed to project documented runtime env into the managed profile `.env`
- **AND** healthy managed profile gateways do not appear stopped solely because upstream gateway service discovery does not match the repo-owned unit names
- **AND** healthy managed profile gateways do not appear stopped because the active interactive Hermes wrapper comes from an older persisted managed-profile revision than the currently booted image
- **AND** intentionally unsupported optional integrations may still report warnings

### Requirement: Managed gateway health reporting matches runtime truth
The workstation SHALL keep operator-facing gateway health output aligned with the actual managed profile runtime.

#### Scenario: Healthy managed profile gateways are reported as running after replacement
- **WHEN** the managed profile gateway services are active after an image replacement with persisted `/home/hermes`
- **THEN** operator-facing health output reports those profile gateways as running
- **AND** status output does not regress to a false stopped state because the managed profile still resolves an older Hermes wrapper generation
