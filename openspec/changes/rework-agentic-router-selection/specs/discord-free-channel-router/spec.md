## MODIFIED Requirements

### Requirement: Managed Discord forced-response sessions use the repo-owned pinned route
The managed Hermes runtime SHALL force configured Discord pinned-response sessions to use the repo-owned route for that channel instead of the runtime's default direct model path or stale session-scoped overrides.

#### Scenario: Free-response message uses the router lane
- **WHEN** a message arrives from a managed Discord free-response channel selected by `GHOSTSHIP_ROUTER_CHANNEL`
- **THEN** the gateway resolves that turn against the local router endpoint
- **AND** the turn uses router alias `agentic`
- **AND** the turn does not fall back to the default direct provider path for that message

#### Scenario: Retired Codex channel env does not create a forced lane
- **WHEN** a message arrives from a managed Discord free-response channel that is not selected by `GHOSTSHIP_ROUTER_CHANNEL`
- **AND** the deployment still sets the retired env key `GHOSTSHIP_CODEX_CHANNEL`
- **THEN** the gateway does not resolve that turn against a repo-owned forced Codex route
- **AND** the turn follows the normal non-pinned runtime routing path for that session

### Requirement: Discord free-response sessions ignore incompatible session model overrides
The managed Hermes runtime SHALL ignore or clear session-scoped model override state for the managed Discord router-pinned free-response session so unsupported custom model switching cannot displace the forced execution path for that channel.

#### Scenario: Existing session override does not displace router pinning
- **WHEN** a Discord free-response session selected by `GHOSTSHIP_ROUTER_CHANNEL` already has cached session-scoped model override state
- **THEN** the managed runtime does not use that override for the next free-response turn
- **AND** the free-response turn still runs on the router-pinned `agentic` path

#### Scenario: Model switch command is rejected in pinned free-response context
- **WHEN** a user issues `/model` inside a managed Discord free-response session selected by `GHOSTSHIP_ROUTER_CHANNEL`
- **THEN** the runtime rejects the switch for that session
- **AND** the runtime reports that the free-response channel is pinned to ghostship-router `agentic`
- **AND** the session does not persist a new model override from that command
