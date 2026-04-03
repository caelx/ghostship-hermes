## ADDED Requirements

### Requirement: Workstation runs on systemd with hermes user services
The agent workstation SHALL run on a `systemd`-based runtime that supports both container-level system services and a `hermes` user manager with persisted user services and timers under the workstation home.

#### Scenario: System services start under systemd
- **WHEN** the workstation container boots
- **THEN** the runtime starts the required container-level services under `systemd`
- **AND** those services replace the previous `s6`-managed runtime path

#### Scenario: Hermes user services live under the persisted home
- **WHEN** maintainers inspect the workstation runtime layout
- **THEN** `hermes` user services and timers are stored under the persisted home profile
- **AND** the `hermes` user manager can start those units after the workstation boots

### Requirement: Workstation reuses Hermes-native profile service behavior where possible
The workstation SHALL preserve Hermes' upstream profile model for command aliases and persistent gateway services unless a specific workstation need requires a documented divergence.

#### Scenario: Profile aliases remain Hermes-native
- **WHEN** maintainers inspect how the workstation exposes per-profile commands
- **THEN** the workstation uses Hermes' native `HERMES_HOME`-scoped profile alias behavior

#### Scenario: Persistent gateways align with Hermes install flow
- **WHEN** maintainers inspect how persistent profile gateway services are installed under systemd
- **THEN** the workstation uses Hermes' native `gateway install` behavior where it satisfies the workstation needs
- **AND** any remaining custom service behavior is documented as an intentional divergence

### Requirement: Invocation path remains local and does not depend on live refresh
The workstation SHALL use already-installed local apps and cached local state during normal command invocation rather than requiring invocation-time network updates.

#### Scenario: Agent app invocation uses local state
- **WHEN** the agent invokes `codex`, `gemini-cli`, `opencode`, `openspec`, or `skills`
- **THEN** the invocation uses the currently installed local workstation version
- **AND** the invocation does not first require a live updater round trip
