## MODIFIED Requirements

### Requirement: Normal invocation uses local installed state
The workstation SHALL use already-installed local apps, persisted local state, and the active managed-runtime identity during normal invocation rather than requiring live network refresh in the hot path or falling back to service-discovery assumptions that do not match the managed image topology.

#### Scenario: Local invocation uses the managed layered toolchain
- **WHEN** the agent invokes `hermes`, `codex`, `gemini`, `opencode`, `agent-browser`, `python3`, `pip`, `fd`, `uv`, `yq`, `tmux`, or related runtime commands
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

#### Scenario: Retired router-primary key does not survive replacement
- **WHEN** the current image contract no longer owns `model.base_url` for the root managed agent and persisted config still contains the older router-primary value
- **THEN** managed convergence removes that retired repo-owned key during boot
- **AND** the resulting managed config no longer routes the direct primary lane through the local router
