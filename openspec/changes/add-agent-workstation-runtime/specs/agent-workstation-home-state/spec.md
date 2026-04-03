## ADDED Requirements

### Requirement: Full workstation home persists across rebuilds and restarts
The agent workstation SHALL treat the full `/home/hermes` profile as durable state so app installs, configs, skills, plugins/extensions, updater metadata, and Hermes state survive container restart and replacement when the same home storage is reused.

#### Scenario: Reused home restores the workstation
- **WHEN** a new container instance starts with the same persisted `/home/hermes`
- **THEN** the workstation sees the previously installed apps, configs, skills, and Hermes state from that home
- **AND** the workstation does not require fresh first-run bootstrap for content already present in the persisted home

#### Scenario: Workstation docs define the persistence contract
- **WHEN** maintainers inspect the workstation documentation
- **THEN** the docs describe `/home/hermes` as the durable workstation root
- **AND** the docs state that rebuilding or restarting the container is expected to preserve that home state

### Requirement: Workstation home is single-writer state
The workstation SHALL assume one active container instance per persisted `/home/hermes` so mutable state is not shared concurrently between multiple running containers.

#### Scenario: Docs warn against concurrent use
- **WHEN** maintainers inspect the workstation persistence guidance
- **THEN** the docs warn that one persisted `/home/hermes` should not be used by multiple running workstation containers at the same time

### Requirement: Boot seeding preserves existing workstation state
Boot-time workstation seeding SHALL copy missing defaults into `/home/hermes` without overwriting existing user-managed files or directories that already exist there.

#### Scenario: Missing default is seeded
- **WHEN** a workstation-managed default file or directory is absent from `/home/hermes`
- **THEN** boot seeding copies it into place

#### Scenario: Existing workstation content is preserved
- **WHEN** the corresponding file or directory already exists in `/home/hermes`
- **THEN** boot seeding leaves the existing content intact unless the seeding rules explicitly mark that path as managed and replaceable
