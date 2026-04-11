## REMOVED Requirements

### Requirement: `feed` state SHALL persist under profile-scoped Hermes storage
**Reason**: The supported image runtime no longer uses named profiles as the storage boundary for the managed agent.
**Migration**: Persist `FEED_DB_PATH` under the single managed Hermes home at `/home/hermes/.hermes`.

## ADDED Requirements

### Requirement: `feed` state SHALL persist under the single managed Hermes home
The `feed` SQLite database SHALL live under the single managed Hermes runtime storage so the agent keeps durable RSS state across container replacement without named-profile isolation rules.

#### Scenario: Managed runtime uses persistent Hermes storage
- **WHEN** the managed Hermes agent runs `feed`
- **THEN** `FEED_DB_PATH` MUST resolve under `/home/hermes/.hermes`
- **AND** the database path MUST be stable across container replacement
- **AND** the runtime does not require a named profile-specific storage path for the supported default workflow
