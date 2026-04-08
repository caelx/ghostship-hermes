## MODIFIED Requirements

### Requirement: Normal invocation uses local installed state
The workstation SHALL use already-installed local apps and persisted local state during normal invocation rather than requiring live network refresh in the hot path.

#### Scenario: Local invocation uses the managed layered toolchain
- **WHEN** the agent invokes `hermes`, `codex`, `gemini-cli`, `opencode`, `agent-browser`, or related runtime commands
- **THEN** the invocation uses the currently installed local state from the managed user Nix profile or the managed persisted npm tool prefix
- **AND** the invocation does not first require a live update round trip during that invocation

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
- **AND** that prefix remains available on `PATH` for the Hermes runtime user across restart and replacement
