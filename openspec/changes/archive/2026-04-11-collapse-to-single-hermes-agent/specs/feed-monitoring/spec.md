## REMOVED Requirements

### Requirement: `feed` state SHALL persist under profile-scoped Hermes storage
**Reason**: The runtime no longer treats named profiles as the supported storage boundary for the managed agent.
**Migration**: Persist `FEED_DB_PATH` under the single managed Hermes home so existing feed state follows the root-managed runtime contract.

## ADDED Requirements

### Requirement: `feed` state SHALL persist under the single managed Hermes home
The `feed` SQLite database SHALL live under the single managed Hermes runtime storage so the agent keeps durable RSS state across container replacement without profile-specific isolation rules.

#### Scenario: Managed runtime uses persistent Hermes storage
- **WHEN** the managed Hermes agent runs `feed`
- **THEN** `FEED_DB_PATH` MUST resolve under `/home/hermes/.hermes`
- **AND** the database path MUST be stable across container replacement
- **AND** the runtime does not require a named profile-specific storage path for the supported default workflow
