## MODIFIED Requirements

### Requirement: Managed Discord forced-response sessions use the repo-owned pinned route
The managed Hermes runtime SHALL force configured Discord pinned-response sessions to use the repo-owned route for that channel instead of the runtime's default direct model path or stale session-scoped overrides.

#### Scenario: Free-response message uses the router lane
- **WHEN** a message arrives from a managed Discord free-response channel
- **THEN** the gateway resolves that turn against the local router endpoint
- **AND** the turn uses router alias `coding`
- **AND** the turn does not fall back to the default direct provider path for that message

#### Scenario: Codex message uses the Codex deep-reasoning lane
- **WHEN** a message arrives from the managed Discord channel selected by `GHOSTSHIP_CODEX_CHANNEL`
- **THEN** the gateway resolves that turn against the `openai-codex` provider
- **AND** the turn uses the `gpt-5.4` model
- **AND** the turn requests high reasoning effort for that channel
- **AND** the turn does not fall back to the default router or direct provider path for that message

### Requirement: Discord free-response sessions ignore incompatible session model overrides
The managed Hermes runtime SHALL ignore or clear session-scoped model override state for Discord pinned-response sessions so unsupported custom model switching cannot displace the forced execution path for that channel.

#### Scenario: Existing session override does not displace router pinning
- **WHEN** a Discord free-response session already has cached session-scoped model override state
- **THEN** the managed runtime does not use that override for the next free-response turn
- **AND** the free-response turn still runs on the router-pinned `coding` path

#### Scenario: Existing session override does not displace Codex pinning
- **WHEN** a Discord session selected by `GHOSTSHIP_CODEX_CHANNEL` already has cached session-scoped model override state
- **THEN** the managed runtime does not use that override for the next Codex-pinned turn
- **AND** the Codex-pinned turn still runs on the pinned Codex `gpt-5.4` high-reasoning path

#### Scenario: Model switch command is rejected in pinned free-response context
- **WHEN** a user issues `/model` inside a managed Discord free-response session
- **THEN** the runtime rejects the switch for that session
- **AND** the runtime reports that the free-response channel is pinned to ghostship-router `coding`
- **AND** the session does not persist a new model override from that command

#### Scenario: Model switch command is rejected in pinned Codex context
- **WHEN** a user issues `/model` inside a managed Discord session selected by `GHOSTSHIP_CODEX_CHANNEL`
- **THEN** the runtime rejects the switch for that session
- **AND** the runtime reports that the Codex channel is pinned to Codex `gpt-5.4`
- **AND** the session does not persist a new model override from that command
