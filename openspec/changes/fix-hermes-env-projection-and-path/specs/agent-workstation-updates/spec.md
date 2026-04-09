## MODIFIED Requirements

### Requirement: Supported doctor warnings are reduced through the managed runtime layers
The workstation SHALL wire the runtime dependencies and shared env needed for the Hermes doctor checks that correspond to intentionally supported features.

#### Scenario: Doctor reflects supported features
- **WHEN** the operator runs `hermes -p <profile> doctor`
- **THEN** the managed runtime reduces avoidable warnings for the supported Hermes, Codex, browser, GitHub-token, Home Assistant, and supported profile-facing env projection paths
- **AND** supported profile-facing integrations do not warn only because bootstrap failed to project documented runtime env into the managed profile `.env`
- **AND** intentionally unsupported optional integrations may still report warnings
