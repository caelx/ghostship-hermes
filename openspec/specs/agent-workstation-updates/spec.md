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
The workstation SHALL keep operator-facing gateway health output aligned with the actual managed single-agent runtime.

#### Scenario: Healthy managed gateway is reported as running after replacement
- **WHEN** the managed gateway service is active after an image replacement with persisted `/home/hermes`
- **THEN** operator-facing health output reports that gateway as running
- **AND** status output does not regress to a false stopped state because `/home/hermes/.hermes/gateway.pid` is missing while the service is active

#### Scenario: Live validation proves the managed gateway marker contract
- **WHEN** maintainers run the Hermes image validation or live post-deploy validation for the managed image
- **THEN** the validation checks that `ghostship-hermes-gateway.service` is active
- **AND** the validation checks that `/home/hermes/.hermes/gateway.pid` exists while that service is active
- **AND** the validation checks that dashboard or Hermes status surfaces report the managed gateway as present from that marker

### Requirement: Image validation proves safe managed-state edits do not restart the gateway
The workstation SHALL validate that routine mutable-state updates under the managed Hermes home do not trigger avoidable managed gateway restarts.

#### Scenario: Validation proves auth updates are non-disruptive
- **WHEN** maintainers run the Hermes image validation suite against the managed single-agent image
- **THEN** the suite mutates `/home/hermes/.hermes/auth.json` in a non-destructive test flow
- **AND** the suite verifies that the running `hermes-gateway.service` process identity does not change solely because of that mutation

#### Scenario: Validation proves SOUL edits are non-disruptive
- **WHEN** maintainers run the Hermes image validation suite against the managed single-agent image
- **THEN** the suite mutates `/home/hermes/.hermes/SOUL.md` in a non-destructive test flow
- **AND** the suite verifies that the running `hermes-gateway.service` process identity does not change solely because of that mutation

#### Scenario: Validation still proves actual restart triggers work
- **WHEN** maintainers run the Hermes image validation suite against the managed single-agent image
- **THEN** the suite still verifies restart-visible behavior for managed `.env` or `config.yaml` changes
- **AND** the narrowed non-restart checks do not replace coverage for the intended restart-triggering paths

### Requirement: Runtime validation proves the native persistent-browser path
The workstation SHALL validate the supported local browser contract with a non-destructive browser smoke that proves stock `agent-browser` can launch the image-native CloakBrowser runtime with the supported persisted profile path.

#### Scenario: Validation exercises native browser launch
- **WHEN** maintainers run the Hermes image validation suite for a build that advertises the native local browser path
- **THEN** the suite executes a non-destructive browser action through stock `agent-browser`
- **AND** that action uses the supported image-native CloakBrowser runtime rather than only proving command discovery

#### Scenario: Validation proves browser profile persistence
- **WHEN** maintainers run restart or container-replacement validation for the workstation image
- **THEN** the suite verifies that the supported browser profile state remains available from the persisted `/home/hermes` tree after the runtime comes back
- **AND** the suite does not treat a fresh empty browser profile after restart as a passing result

### Requirement: Validation excludes retired browser surfaces
The workstation SHALL stop treating retired browser shims as proof of the supported browser contract.

#### Scenario: Validation does not require Camofox-only health endpoints
- **WHEN** maintainers run image or live validation for the supported browser path
- **THEN** the validation does not require Camofox-specific health endpoints, cache markers, or helper modules to pass

#### Scenario: Validation does not require manager-wrapper browser APIs
- **WHEN** maintainers run image or live validation for the supported browser path
- **THEN** the validation does not require `ghostship-cloakbrowser` commands or CloakBrowser Manager API calls to pass
