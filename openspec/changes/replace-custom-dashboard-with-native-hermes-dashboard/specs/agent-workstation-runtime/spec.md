## ADDED Requirements

### Requirement: Managed browser runtime uses the upstream Hermes dashboard process
The workstation SHALL launch the browser surface through the upstream Hermes dashboard command from the pinned Hermes runtime instead of through a repo-owned dashboard controller package.

#### Scenario: Managed browser service starts the upstream Hermes dashboard
- **WHEN** the managed image starts its browser service for the Hermes runtime
- **THEN** the service executes the upstream Hermes dashboard command from the pinned Hermes runtime or wrapper
- **AND** the service does not depend on the retired `packages/hermes-dashboard` package or a Ghostship-specific HTTP controller process
- **AND** the service disables automatic browser opening for non-interactive container startup

### Requirement: Managed browser runtime adopts the upstream dashboard port
The workstation SHALL treat the upstream Hermes dashboard port `9119` as the browser runtime contract instead of the repo-owned `7681` dashboard port.

#### Scenario: Managed image publishes the upstream dashboard port
- **WHEN** maintainers inspect the managed image runtime, docs, firewall rules, or health checks after this change
- **THEN** the browser runtime contract uses port `9119`
- **AND** the runtime does not keep `7681` as the supported dashboard port
- **AND** validation and deployment guidance align to the upstream port contract

### Requirement: Managed browser runtime permits required cross-origin iframe embedding
The workstation SHALL preserve the runtime/header behavior needed for the upstream Hermes dashboard to load and function when embedded inside a cross-origin iframe for the supported deployment workflow.

#### Scenario: Browser runtime does not deny required iframe embedding
- **WHEN** the managed browser runtime serves the upstream Hermes dashboard for the deployed image
- **THEN** the response headers and runtime policy do not block the supported cross-origin iframe embed path
- **AND** the runtime still serves the upstream Hermes dashboard process rather than a repo-owned browser replacement

### Requirement: Managed browser runtime removes the browser-terminal sidecar contract
The workstation SHALL not require a repo-owned browser-terminal sidecar such as `ttyd` to satisfy the supported dashboard runtime surface.

#### Scenario: Browser runtime comes up without ttyd coupling
- **WHEN** maintainers inspect the managed browser runtime dependency graph after this change
- **THEN** the dashboard runtime path does not require the retired same-origin `ttyd` proxy contract
- **AND** browser-terminal startup or websocket proxy behavior is not part of the supported dashboard runtime surface
