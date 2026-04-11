## ADDED Requirements

### Requirement: Runtime seeding converges one managed skill tree
The workstation SHALL seed one repo-managed Hermes skill tree for the single managed agent instead of splitting runtime-owned seed content across shared and per-profile destinations.

#### Scenario: Fresh managed runtime receives one skill tree
- **WHEN** a fresh managed runtime boots with an empty managed Hermes home
- **THEN** bootstrap seeds the approved repo-managed skills into one canonical destination under `/home/hermes/.hermes`
- **AND** the runtime does not require separate shared and profile-specific skill destinations for the supported default workflow

#### Scenario: Existing managed skill content remains authoritative after first seed
- **WHEN** a repo-managed skill directory already exists at the canonical managed destination
- **THEN** bootstrap leaves that runtime-owned skill directory intact unless an explicit seed-management rule says it is still repo-managed
- **AND** the default seeding flow does not overwrite runtime-owned skill content just because the source seed changed

### Requirement: Runtime seeding converges one managed `SOUL.md`
The workstation SHALL seed one managed `SOUL.md` for the single managed agent instead of maintaining profile-local prompt files.

#### Scenario: Fresh managed runtime receives one seed-managed `SOUL.md`
- **WHEN** a fresh managed runtime boots with no live `SOUL.md`
- **THEN** bootstrap installs the repo-managed `SOUL.md` into one canonical destination under `/home/hermes/.hermes`
- **AND** the supported runtime contract does not require per-profile `SOUL.md` files

#### Scenario: Seed-managed `SOUL.md` preserves later live edits
- **WHEN** the managed `SOUL.md` has been edited by an operator or agent after the initial seed
- **THEN** later bootstrap runs do not overwrite that live file unless the repo still owns it under the seed-management rules
- **AND** the runtime continues treating the live single-agent `SOUL.md` as authoritative
