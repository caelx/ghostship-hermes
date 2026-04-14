## ADDED Requirements

### Requirement: Managed Discord forced-response sessions use the repo-owned pinned route
The managed Hermes runtime SHALL force configured Discord pinned-response sessions to use the repo-owned route for that channel instead of the runtime's default direct model path or stale session-scoped overrides.

#### Scenario: Free-response message uses the router lane
- **WHEN** a message arrives from a managed Discord free-response channel
- **THEN** the gateway resolves that turn against the local router endpoint
- **AND** the turn uses the repo-approved router alias
- **AND** the turn does not fall back to the default direct provider path for that message

#### Scenario: Deepthink message uses the Codex deep-reasoning lane
- **WHEN** a message arrives from the managed Discord `#deepthink` channel
- **THEN** the gateway resolves that turn against the `openai-codex` provider
- **AND** the turn uses the `gpt-5.4` model
- **AND** the turn requests high reasoning effort for that channel
- **AND** the turn does not fall back to the default router or direct provider path for that message

### Requirement: Discord free-response sessions ignore incompatible session model overrides
The managed Hermes runtime SHALL ignore or clear session-scoped model override state for Discord pinned-response sessions so unsupported custom model switching cannot displace the forced execution path for that channel.

#### Scenario: Existing session override does not displace router pinning
- **WHEN** a Discord free-response session already has cached session-scoped model override state
- **THEN** the managed runtime does not use that override for the next free-response turn
- **AND** the free-response turn still runs on the router-pinned path

#### Scenario: Existing session override does not displace deepthink pinning
- **WHEN** a Discord `#deepthink` session already has cached session-scoped model override state
- **THEN** the managed runtime does not use that override for the next `#deepthink` turn
- **AND** the `#deepthink` turn still runs on the pinned Codex `gpt-5.4` high-reasoning path

#### Scenario: Model switch command is rejected in pinned free-response context
- **WHEN** a user issues `/model` inside a managed Discord free-response session
- **THEN** the runtime rejects the switch for that session
- **AND** the runtime reports that the free-response channel is pinned to the router-managed path
- **AND** the session does not persist a new model override from that command

#### Scenario: Model switch command is rejected in pinned deepthink context
- **WHEN** a user issues `/model` inside a managed Discord `#deepthink` session
- **THEN** the runtime rejects the switch for that session
- **AND** the runtime reports that the `#deepthink` channel is pinned to Codex `gpt-5.4`
- **AND** the session does not persist a new model override from that command
