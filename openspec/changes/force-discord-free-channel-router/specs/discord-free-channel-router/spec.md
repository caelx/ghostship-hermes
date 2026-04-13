## ADDED Requirements

### Requirement: Managed Discord free-response sessions use the local router
The managed Hermes runtime SHALL force Discord free-response sessions to use the local `ghostship-hermes-router` endpoint instead of the managed profile's default direct model path.

#### Scenario: Free-response message uses the router lane
- **WHEN** a message arrives from a managed Discord free-response channel
- **THEN** the gateway resolves that turn against `http://127.0.0.1:8788/v1`
- **AND** the turn uses the repo-approved router alias `agentic`
- **AND** the turn does not fall back to the profile's default direct provider path for that message

### Requirement: Discord free-response sessions ignore incompatible session model overrides
The managed Hermes runtime SHALL ignore or clear session-scoped model override state for Discord free-response sessions so unsupported custom model switching cannot displace the router-pinned execution path.

#### Scenario: Existing session override does not displace router pinning
- **WHEN** a Discord free-response session already has cached session-scoped model override state
- **THEN** the managed runtime does not use that override for the next free-response turn
- **AND** the free-response turn still runs on the router-pinned `agentic` path

#### Scenario: Model switch command is rejected in pinned free-response context
- **WHEN** a user issues `/model` inside a managed Discord free-response session
- **THEN** the runtime rejects the switch for that session
- **AND** the runtime reports that the free-response channel is pinned to the router-managed path
- **AND** the session does not persist a new model override from that command
