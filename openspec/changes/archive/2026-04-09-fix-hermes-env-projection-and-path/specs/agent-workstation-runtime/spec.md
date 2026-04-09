## MODIFIED Requirements

### Requirement: Normal invocation uses local installed state
The workstation SHALL use already-installed local apps and persisted local state during normal invocation rather than requiring live network refresh in the hot path.

#### Scenario: Local invocation uses the managed layered toolchain
- **WHEN** the agent invokes `hermes`, `codex`, `gemini-cli`, `opencode`, `agent-browser`, or related runtime commands
- **THEN** the invocation uses the currently installed local state from the managed user Nix profile or the managed persisted npm tool prefix
- **AND** the Hermes-user runtime contract exposes `/home/hermes/.local/bin` and the managed user profile bin on the normal invocation path for those commands
- **AND** the invocation does not first require a live update round trip during that invocation

### Requirement: Runtime exposes a managed persisted npm tool prefix
The workstation SHALL expose a persisted npm-managed tool prefix on the Hermes user `PATH` for fast-moving agent CLIs that are intentionally updated outside the image closure.

#### Scenario: Managed npm tool prefix survives restart and replacement
- **WHEN** the container boots with persisted `/home/hermes`
- **THEN** the runtime prepares a managed npm tool prefix and cache under `/home/hermes`
- **AND** `/home/hermes/.local/bin` remains available on the Hermes-user default invocation path across restart and replacement
- **AND** that prefix remains available on `PATH` for the Hermes runtime user across restart and replacement
