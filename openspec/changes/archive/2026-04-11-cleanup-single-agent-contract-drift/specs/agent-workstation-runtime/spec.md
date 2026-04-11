## MODIFIED Requirements

### Requirement: Normal invocation uses local installed state
The workstation SHALL use already-installed local apps, persisted local state, and the active managed-runtime identity during normal invocation rather than requiring live network refresh in the hot path or falling back to service-discovery assumptions that do not match the managed image topology.

#### Scenario: Local invocation uses the managed layered toolchain
- **WHEN** the agent invokes `hermes`, `codex`, `opencode`, `agent-browser`, `python3`, `pip`, `fd`, `uv`, `yq`, `tmux`, or related runtime commands
- **THEN** the invocation uses the currently installed local state from the managed user Nix profile or the managed persisted npm tool prefix
- **AND** the Hermes-user runtime contract exposes `/home/hermes/.local/bin` and the managed user profile bin on the normal invocation path for those commands
- **AND** `agent-browser` may be satisfied by the image-managed runtime layer instead of the mutable npm-managed tool layer when the image declares it as a supported exception
- **AND** the invocation does not first require a live update round trip during that invocation

#### Scenario: Managed Hermes invocation sees managed runtime identity
- **WHEN** an operator runs `hermes ...` inside the managed image
- **THEN** the root managed Hermes home exposes the managed-runtime marker or equivalent managed identity that Hermes checks for interactive commands
- **AND** the invocation does not require switching into a repo-owned named profile to discover the supported managed runtime behavior

#### Scenario: Image replacement converges the active Hermes wrapper generation
- **WHEN** the workstation boots after replacing the image while `/home/hermes` persists
- **THEN** the `hermes` executable that resolves from the managed Hermes-user PATH matches the currently booted repo-managed wrapper generation
- **AND** a stale persisted `hermes-agent-wrapped` entry does not continue shadowing newer baked runtime behavior from the replacement image

#### Scenario: Image replacement converges repo-managed persisted system config
- **WHEN** the workstation boots after replacing the image while repo-managed system config persists under `/home/hermes`
- **THEN** repo-owned persisted runtime config that is meant to track the current image generation is reconciled to the current contract during managed convergence
- **AND** stale persisted repo-managed values do not continue shadowing newer baked or bootstrap-defined runtime behavior from the replacement image

### Requirement: Local Hermes browser default resolves to a working agent-browser command
The workstation SHALL keep Hermes local browser workflows pointed at `agent-browser` while ensuring that the resolved command launches a working backend on supported image architectures.

#### Scenario: Local browser default stays anchored on agent-browser
- **WHEN** maintainers inspect the managed single-agent config or operators inspect the managed agent browser configuration
- **THEN** Hermes local browser mode remains the default browser path
- **AND** that default continues to use `agent-browser` as the local browser command rather than switching to a different provider to avoid this bug

#### Scenario: Operator-facing agent-browser command launches successfully
- **WHEN** the operator invokes `agent-browser` from the managed Hermes-user PATH in a supported image
- **THEN** the resolved command launches a working backend for that image architecture
- **AND** the managed runtime does not prefer a broken mutable npm shim over a working image-managed `agent-browser` binary

## REMOVED Requirements

### Requirement: Managed gateway commands align with repo-owned profile services
**Reason**: The supported image topology no longer uses a repo-owned fleet of named-profile gateway services.
**Migration**: Route interactive gateway status and control guidance through the single managed gateway service contract.

## ADDED Requirements

### Requirement: Managed gateway commands align with the repo-owned single-agent service
The workstation SHALL align interactive gateway commands with the repo-owned single-agent managed gateway service instead of treating the image as an upstream user-service installation or a fleet of named profile services.

#### Scenario: Managed gateway status reflects the repo-owned single-agent unit
- **WHEN** an operator runs `hermes gateway status` inside the managed image
- **THEN** the command reports the state of the repo-owned managed gateway service for the single agent
- **AND** it does not claim the gateway is stopped solely because an upstream user-scoped Hermes service is absent

#### Scenario: Managed control paths do not suggest upstream user-service recovery
- **WHEN** an operator runs `hermes gateway start`, `stop`, or `restart` inside the managed image
- **THEN** the command either targets the correct repo-owned managed service or exits with explicit managed-runtime guidance
- **AND** it does not instruct the operator to use `systemctl --user`, `loginctl enable-linger`, or upstream `hermes gateway install` flows
