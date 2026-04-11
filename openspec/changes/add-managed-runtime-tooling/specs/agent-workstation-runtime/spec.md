## MODIFIED Requirements

### Requirement: Normal invocation uses local installed state
The workstation SHALL use already-installed local apps, persisted local state, and the active managed-runtime identity during normal invocation rather than requiring live network refresh in the hot path or falling back to service-discovery assumptions that do not match the managed image topology.

#### Scenario: Local invocation uses the managed layered toolchain
- **WHEN** the agent invokes `hermes`, `codex`, `opencode`, `agent-browser`, `python3`, `pip`, `fd`, `uv`, `yq`, `tmux`, or related runtime commands
- **THEN** the invocation uses the currently installed local state from the managed user Nix profile or the managed persisted npm tool prefix
- **AND** the Hermes-user runtime contract exposes `/home/hermes/.local/bin` and the managed user profile bin on the normal invocation path for those commands
- **AND** `agent-browser` may be satisfied by the image-managed runtime layer instead of the mutable npm-managed tool layer when the image declares it as a supported exception
- **AND** the invocation does not first require a live update round trip during that invocation

## ADDED Requirements

### Requirement: Managed user tooling includes a pip-capable Python runtime
The workstation SHALL treat Python packaging support as part of the managed Hermes-user runtime toolchain rather than a partial image-layer fallback.

#### Scenario: Mutable Python tooling lives in the managed runtime layer
- **WHEN** maintainers inspect the runtime contract for Hermes and operator-facing CLI tools
- **THEN** the supported `python3`, `pip`, and `python3 -m pip` workflow comes from the managed user profile layer
- **AND** the runtime does not rely on a separate image-only `pip` exception to provide that workflow
