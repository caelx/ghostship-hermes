## MODIFIED Requirements

### Requirement: Supported doctor warnings are reduced through the managed runtime layers
The workstation SHALL wire the runtime dependencies, managed-state markers, and shared env needed for Hermes operator health reporting so the checks that correspond to intentionally supported features reflect the real managed runtime state.

#### Scenario: Doctor reflects supported features
- **WHEN** the operator runs `hermes doctor`
- **THEN** the managed runtime reduces avoidable warnings for the supported Hermes, Codex, browser, GitHub-token, Home Assistant, and supported managed-env projection paths
- **AND** supported integrations do not warn only because bootstrap failed to project documented runtime env into the managed `.env`
- **AND** the healthy managed gateway does not appear stopped solely because upstream gateway service discovery does not match the repo-owned unit name
- **AND** the healthy managed gateway does not appear stopped because the active interactive Hermes wrapper comes from an older persisted managed-runtime revision than the currently booted image
- **AND** the supported browser path does not regress into warnings solely because `agent-browser` is provided from the image-managed runtime layer instead of the mutable npm layer
- **AND** intentionally unsupported optional integrations may still report warnings

## ADDED Requirements

### Requirement: Managed tooling refresh may keep supported CLI exceptions outside the npm layer
The workstation SHALL allow the managed user-tooling refresh contract to keep specific supported CLIs on the operator PATH from the image/runtime layer when the mutable npm delivery path is not the supported execution source.

#### Scenario: Managed refresh preserves an image-managed agent-browser exception
- **WHEN** the managed user-tooling refresh converges the Hermes runtime tooling project
- **THEN** the refresh may omit `agent-browser` from the mutable npm-managed CLI set while keeping `agent-browser` available on the operator PATH from the supported image/runtime layer
- **AND** the refresh removes or rewrites stale home-local shims that would otherwise keep pointing `agent-browser` at an unsupported mutable npm install

### Requirement: Runtime validation executes supported CLI entrypoints
The workstation SHALL validate supported runtime CLI execution with command-level smoke tests when command discovery alone is insufficient to prove the runtime path works.

#### Scenario: Agent-browser validation executes the command
- **WHEN** maintainers run the Hermes image validation suite for a build that advertises `agent-browser` on the supported runtime path
- **THEN** the suite executes `agent-browser --help` or an equivalent non-destructive smoke command
- **AND** the suite does not treat a passing `command -v agent-browser` check by itself as sufficient proof that the supported browser command works

### Requirement: Managed gateway health reporting matches runtime truth
The workstation SHALL keep operator-facing gateway health output aligned with the actual managed runtime.

#### Scenario: Healthy managed gateway is reported as running after replacement
- **WHEN** the managed gateway service is active after an image replacement with persisted `/home/hermes`
- **THEN** operator-facing health output reports that gateway as running
- **AND** status output does not regress to a false stopped state because the managed runtime still resolves an older Hermes wrapper generation

#### Scenario: Managed runtime guidance replaces upstream recovery instructions
- **WHEN** the operator asks Hermes for managed gateway status or recovery guidance inside the image
- **THEN** the guidance references the repo-managed single-agent runtime contract
- **AND** it does not recommend upstream user-service recovery steps that are incompatible with the image's managed systemd topology
