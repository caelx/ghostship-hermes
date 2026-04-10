## MODIFIED Requirements

### Requirement: Normal invocation uses local installed state
The workstation SHALL use already-installed local apps, persisted local state, and the active managed-runtime identity during normal invocation rather than requiring live network refresh in the hot path or falling back to service-discovery assumptions that do not match the managed image topology.

#### Scenario: Local invocation uses the managed layered toolchain
- **WHEN** the agent invokes `hermes`, `codex`, `opencode`, `agent-browser`, or related runtime commands
- **THEN** the invocation uses the currently installed local state from the managed user Nix profile or the managed persisted npm tool prefix
- **AND** the Hermes-user runtime contract exposes `/home/hermes/.local/bin` and the managed user profile bin on the normal invocation path for those commands
- **AND** `agent-browser` may be satisfied by the image-managed runtime layer instead of the mutable npm-managed tool layer when the image declares it as a supported exception
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

## ADDED Requirements

### Requirement: Local Hermes browser default resolves to a working agent-browser command
The workstation SHALL keep Hermes local browser workflows pointed at `agent-browser` while ensuring that the resolved command launches a working backend on supported image architectures.

#### Scenario: Local browser default stays anchored on agent-browser
- **WHEN** maintainers inspect the managed Hermes profile scaffold or operators inspect the active profile browser configuration
- **THEN** Hermes local browser mode remains the default browser path
- **AND** that default continues to use `agent-browser` as the local browser command rather than switching to a different provider to avoid this bug

#### Scenario: Operator-facing agent-browser command launches successfully
- **WHEN** the operator invokes `agent-browser` from the managed Hermes-user PATH in a supported image
- **THEN** the resolved command launches a working backend for that image architecture
- **AND** the managed runtime does not prefer a broken mutable npm shim over a working image-managed `agent-browser` binary
