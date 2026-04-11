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

## ADDED Requirements

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

### Requirement: Runtime keeps only a minimum viable immutable system layer
The workstation SHALL keep only the minimum system-layer packages needed to boot, supervise services, expose the browser/router runtime surface, and provide a small approved set of baked admin/debug CLIs.

#### Scenario: Most user-facing tools live outside the immutable system layer
- **WHEN** maintainers inspect the runtime contract for Hermes and operator-facing CLI tools
- **THEN** the immutable image layer does not remain the primary home for broadly updateable user-facing tools such as `hermes`, `curl`, `jq`, `python3`, `nix`, `ripgrep`, and `node`/`npm`
- **AND** those tools are instead expected through managed user-facing runtime layers unless the repo explicitly approves them as baked image tools

#### Scenario: Approved admin CLIs may remain baked into the image layer
- **WHEN** maintainers inspect the default-image runtime contract for operator/admin tools
- **THEN** the immutable image layer may include the repo-approved admin/debug CLI set such as `git`, `gh`, and the OpenSSH client tools
- **AND** those approved baked tools do not by themselves redefine the image as the primary home for the broader mutable user-facing tool surface

### Requirement: Runtime exposes a managed persisted npm tool prefix
The workstation SHALL expose a persisted npm-managed tool prefix on the Hermes user `PATH` for fast-moving agent CLIs that are intentionally updated outside the image closure.

#### Scenario: Managed npm tool prefix survives restart and replacement
- **WHEN** the container boots with persisted `/home/hermes`
- **THEN** the runtime prepares a managed npm tool prefix and cache under `/home/hermes`
- **AND** `/home/hermes/.local/bin` remains available on the Hermes-user default invocation path across restart and replacement
- **AND** that prefix remains available on `PATH` for the Hermes runtime user across restart and replacement


### Requirement: Managed user tooling includes a pip-capable Python runtime
The workstation SHALL treat Python packaging support as part of the managed Hermes-user runtime toolchain rather than a partial image-layer fallback.

#### Scenario: Mutable Python tooling lives in the managed runtime layer
- **WHEN** maintainers inspect the runtime contract for Hermes and operator-facing CLI tools
- **THEN** the supported `python3`, `pip`, and `python3 -m pip` workflow comes from the managed user profile layer
- **AND** the runtime does not rely on a separate image-only `pip` exception to provide that workflow

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
