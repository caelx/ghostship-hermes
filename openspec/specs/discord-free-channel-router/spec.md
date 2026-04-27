## MODIFIED Requirements

### Requirement: Managed Discord Codex sessions use the repo-owned pinned route
The managed Hermes runtime SHALL force the Discord channel selected by `GHOSTSHIP_CODEX_CHANNEL` to use `openai-codex/gpt-5.5` instead of the runtime's default router-backed model path or stale session-scoped overrides.

#### Scenario: Codex-channel message uses the Codex lane
- **WHEN** a message arrives from the Discord channel selected by `GHOSTSHIP_CODEX_CHANNEL`
- **THEN** the gateway resolves that turn against the `openai-codex` provider
- **AND** the turn uses model `gpt-5.5`
- **AND** the turn inherits the normal Hermes reasoning configuration

#### Scenario: Threaded Codex-channel message keeps the Codex lane
- **WHEN** Discord auto-threading creates or receives a thread whose parent channel is selected by `GHOSTSHIP_CODEX_CHANNEL`
- **THEN** the gateway records the parent channel id on `SessionSource.chat_id_alt`
- **AND** the gateway resolves that thread turn against the `openai-codex/gpt-5.5` pinned route

### Requirement: Discord Codex sessions ignore incompatible session model overrides
The managed Hermes runtime SHALL ignore or clear session-scoped model override state for the managed Discord Codex-pinned session so model switching cannot displace the forced execution path for that channel.

#### Scenario: Existing session override does not displace Codex pinning
- **WHEN** a Discord session selected by `GHOSTSHIP_CODEX_CHANNEL` already has cached session-scoped model override state
- **THEN** the managed runtime does not use that override for the next turn
- **AND** the turn still runs on the Codex-pinned `gpt-5.5` path

#### Scenario: Model switch command is rejected in pinned Codex context
- **WHEN** a user issues `/model` inside a managed Discord session selected by `GHOSTSHIP_CODEX_CHANNEL`, including a thread whose parent is selected by `GHOSTSHIP_CODEX_CHANNEL`
- **THEN** the runtime rejects the switch for that session
- **AND** the runtime reports that the channel is pinned to `openai-codex/gpt-5.5`
- **AND** the session does not persist a new model override from that command

### Requirement: Closed Discord thread sessions are retired automatically
The managed Hermes runtime SHALL retire dead Discord thread sessions after 05:00 local Hermes time without deleting historical transcripts.

#### Scenario: Dead thread session mapping is removed
- **WHEN** the daily sweep sees a Discord thread session whose thread is archived, locked, deleted, or inaccessible
- **AND** the session has no running turn or active background process
- **THEN** the runtime flushes memories when possible
- **AND** the runtime removes only the live `sessions.json` mapping for that session
- **AND** historical SQLite transcripts remain intact
- **AND** cached idle agent state and session model override state for that session are cleared
