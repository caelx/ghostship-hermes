## MODIFIED Requirements

### Requirement: Normal invocation uses local installed state
The workstation SHALL use already-installed local apps, persisted local state, and the active managed-runtime identity during normal invocation rather than requiring live network refresh in the hot path or falling back to service-discovery assumptions that do not match the managed image topology.

#### Scenario: Local invocation uses the managed layered toolchain
- **WHEN** the agent invokes `hermes`, `codex`, `gemini-cli`, `opencode`, `agent-browser`, or related runtime commands
- **THEN** the invocation uses the currently installed local state from the managed user Nix profile or the managed persisted npm tool prefix
- **AND** the Hermes-user runtime contract exposes `/home/hermes/.local/bin` and the managed user profile bin on the normal invocation path for those commands
- **AND** the invocation does not first require a live update round trip during that invocation

#### Scenario: Profile-scoped Hermes invocation sees managed runtime identity
- **WHEN** an operator runs `hermes -p <profile> ...` inside the managed image
- **THEN** the active profile home exposes the managed-runtime marker or equivalent managed identity that Hermes checks for interactive commands
- **AND** the invocation does not fall back to upstream user-service assumptions solely because it switched from the root `HERMES_HOME` to a managed profile home

## ADDED Requirements

### Requirement: Runtime keeps only a minimum viable immutable system layer
The workstation SHALL keep only the minimum system-layer packages needed to boot, supervise services, and expose the browser/router runtime surface.

#### Scenario: User-facing tools live outside the immutable system layer
- **WHEN** maintainers inspect the runtime contract for Hermes and operator-facing CLI tools
- **THEN** the immutable image layer does not remain the primary home for updateable user-facing tools such as `hermes`, `git`, `curl`, `jq`, `python3`, `nix`, `ripgrep`, and `node`/`npm`
- **AND** those tools are instead expected through managed user-facing runtime layers

### Requirement: Runtime exposes a managed persisted npm tool prefix
The workstation SHALL expose a persisted npm-managed tool prefix on the Hermes user `PATH` for fast-moving agent CLIs that are intentionally updated outside the image closure.

#### Scenario: Managed npm tool prefix survives restart and replacement
- **WHEN** the container boots with persisted `/home/hermes`
- **THEN** the runtime prepares a managed npm tool prefix and cache under `/home/hermes`
- **AND** `/home/hermes/.local/bin` remains available on the Hermes-user default invocation path across restart and replacement
- **AND** that prefix remains available on `PATH` for the Hermes runtime user across restart and replacement

### Requirement: Managed gateway commands align with repo-owned profile services
The workstation SHALL align interactive gateway commands for managed profiles with the repo-owned `ghostship-hermes-profile-*` services instead of treating the image as an upstream user-service installation.

#### Scenario: Managed profile status reflects the repo-owned gateway unit
- **WHEN** an operator runs `hermes -p <profile> gateway status` for a managed profile
- **THEN** the command reports the state of the matching repo-owned managed gateway service
- **AND** it does not claim the gateway is stopped solely because an upstream `hermes-gateway-<profile>` unit is absent

#### Scenario: Root-scoped gateway status does not misclassify managed services
- **WHEN** an operator runs `hermes gateway status` from the root managed home in the image
- **THEN** the command reports managed profile gateway state using the image's multi-profile topology
- **AND** it does not describe a managed profile gateway process as a manual foreground gateway

#### Scenario: Managed control paths do not suggest upstream user-service recovery
- **WHEN** an operator runs `hermes -p <profile> gateway start`, `stop`, or `restart` inside the managed image
- **THEN** the command either targets the correct repo-owned managed service or exits with explicit managed-runtime guidance
- **AND** it does not instruct the operator to use `systemctl --user`, `loginctl enable-linger`, or upstream `hermes gateway install` flows for that managed profile
