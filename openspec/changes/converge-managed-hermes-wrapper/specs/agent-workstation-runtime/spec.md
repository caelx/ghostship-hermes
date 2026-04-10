## MODIFIED Requirements

### Requirement: Normal invocation uses local installed state
The workstation SHALL use already-installed local apps, persisted local state, and the active managed-runtime identity during normal invocation rather than requiring live network refresh in the hot path or falling back to service-discovery assumptions that do not match the managed image topology.

#### Scenario: Local invocation uses the managed layered toolchain
- **WHEN** the agent invokes `hermes`, `codex`, `opencode`, `agent-browser`, or related runtime commands
- **THEN** the invocation uses the currently installed local state from the managed user Nix profile or the managed persisted npm tool prefix
- **AND** the Hermes-user runtime contract exposes `/home/hermes/.local/bin` and the managed user profile bin on the normal invocation path for those commands
- **AND** the invocation does not first require a live update round trip during that invocation

#### Scenario: Profile-scoped Hermes invocation sees managed runtime identity
- **WHEN** an operator runs `hermes -p <profile> ...` inside the managed image
- **THEN** the active profile home exposes the managed-runtime marker or equivalent managed identity that Hermes checks for interactive commands
- **AND** the invocation does not fall back to upstream user-service assumptions solely because it switched from the root `HERMES_HOME` to a managed profile home

#### Scenario: Image replacement converges the active Hermes wrapper generation
- **WHEN** the workstation boots after replacing the image while `/home/hermes` persists
- **THEN** the `hermes` executable that resolves from the managed Hermes-user PATH matches the currently booted repo-managed wrapper generation
- **AND** a stale persisted `hermes-agent-wrapped` entry does not continue shadowing newer baked runtime behavior from the replacement image

#### Scenario: Image replacement converges repo-managed persisted system config
- **WHEN** the workstation boots after replacing the image while repo-managed system config persists under `/home/hermes`
- **THEN** repo-owned persisted runtime config that is meant to track the current image generation is reconciled to the current contract during managed convergence
- **AND** stale persisted repo-managed values do not continue shadowing newer baked or bootstrap-defined runtime behavior from the replacement image

### Requirement: Managed gateway commands align with repo-owned profile services
The workstation SHALL align interactive gateway commands for managed profiles with the repo-owned `ghostship-hermes-profile-*` services instead of treating the image as an upstream user-service installation.

#### Scenario: Managed profile status reflects the repo-owned gateway unit
- **WHEN** an operator runs `hermes -p <profile> gateway status` for a managed profile
- **THEN** the command reports the state of the matching repo-owned managed gateway service
- **AND** it does not claim the gateway is stopped solely because an upstream `hermes-gateway-<profile>` unit is absent
