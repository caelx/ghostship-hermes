## MODIFIED Requirements

### Requirement: Normal invocation uses local installed state
The workstation SHALL use already-installed local apps, persisted local state, and the active managed-runtime identity during normal invocation rather than requiring live network refresh in the hot path or falling back to service-discovery assumptions that do not match the managed image topology.

#### Scenario: Local invocation uses the managed layered toolchain
- **WHEN** the agent invokes `hermes`, `codex`, `opencode`, `agent-browser`, or related runtime commands
- **THEN** the invocation uses the currently installed local state from the managed user Nix profile or the managed persisted npm tool prefix
- **AND** the Hermes-user runtime contract exposes `/home/hermes/.local/bin` and the managed user profile bin on the normal invocation path for those commands
- **AND** `agent-browser` may be satisfied by the image-managed runtime layer instead of the mutable npm-managed tool layer when the image declares it as a supported exception
- **AND** the invocation does not first require a live update round trip during that invocation

#### Scenario: Managed Hermes invocation sees one runtime identity
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

## REMOVED Requirements

### Requirement: Managed gateway commands align with repo-owned profile services
**Reason**: The runtime no longer treats a fleet of repo-owned named-profile gateway services as the supported topology.
**Migration**: Replace profile-scoped gateway guidance and `hermes -p <profile> gateway ...` workflows with the single managed gateway service contract.

### Requirement: Managed profile env excludes fixed Chaptarr and n8n path/version selector defaults
**Reason**: The runtime no longer exposes a profile-scoped env contract; the allowlist now applies to one managed env file for the single agent.
**Migration**: Preserve the same exclusion rule under the single-agent env contract and update docs/examples to reference the root managed env file.

## ADDED Requirements

### Requirement: Managed gateway commands align with the repo-owned single-agent service
The workstation SHALL align interactive gateway commands with the repo-owned single-agent managed gateway service instead of treating the image as an upstream user-service installation or a fleet of named profile services.

#### Scenario: Managed gateway status reflects the repo-owned single-agent unit
- **WHEN** an operator runs `hermes gateway status` inside the managed image
- **THEN** the command reports the state of the matching repo-owned managed gateway service for the single agent
- **AND** it does not claim the gateway is stopped solely because an upstream user-scoped Hermes service is absent

#### Scenario: Managed control paths do not suggest upstream user-service recovery
- **WHEN** an operator runs `hermes gateway start`, `stop`, or `restart` inside the managed image
- **THEN** the command either targets the correct repo-owned managed service or exits with explicit managed-runtime guidance
- **AND** it does not instruct the operator to use `systemctl --user`, `loginctl enable-linger`, or upstream `hermes gateway install` flows

### Requirement: Managed runtime env excludes fixed Chaptarr and n8n path/version selector defaults
The workstation SHALL keep fixed Chaptarr and n8n API path/version defaults out of the managed single-agent env contract.

#### Scenario: Managed runtime does not project fixed path/version vars
- **WHEN** bootstrap writes the managed single-agent `.env` contract or docs describe the supported env surface
- **THEN** the runtime does not project `CHAPTARR_API_PATH`, `CHAPTARR_API_VERSION`, `N8N_PUBLIC_API_ENDPOINT`, or `N8N_PUBLIC_API_VERSION`
- **AND** the supported operator-facing contract continues to use only the base URL and credentials for those services

#### Scenario: Chaptarr and n8n docs assume the default API layout
- **WHEN** maintainers inspect Chaptarr or n8n runtime/API documentation
- **THEN** the docs describe the default `/api/v1` layout directly
- **AND** they do not present those fixed path/version selectors as optional managed runtime env knobs
