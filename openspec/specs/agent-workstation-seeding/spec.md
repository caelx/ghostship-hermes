## ADDED Requirements

### Requirement: Workstation seeding targets persisted locations
The workstation SHALL seed repo-managed defaults into persisted destinations under `/opt/data` and `/opt/data/home` rather than into ephemeral image paths under `/home/hermes`.

#### Scenario: Fresh workstation receives defaults in persisted storage
- **WHEN** a fresh workstation boots with an empty `/opt/data`
- **THEN** the runtime seeds Hermes defaults into `/opt/data`
- **AND** the runtime seeds HOME-anchored workstation defaults into `/opt/data/home`

### Requirement: Seeding is copy-if-missing and non-destructive
The workstation SHALL copy defaults only when the persisted destination is missing and SHALL NOT overwrite existing persisted user content during boot.

#### Scenario: Missing seed file is created
- **WHEN** a repo-managed seed file does not exist in the persisted destination
- **THEN** boot seeding creates it there

#### Scenario: Existing persisted file is preserved
- **WHEN** the persisted destination already contains that file or directory
- **THEN** boot seeding leaves the persisted content unchanged

### Requirement: Seeded workstation defaults mirror the repo-managed develop environment subset
The workstation SHALL seed the selected repo-managed develop-environment defaults needed for Hermes, `.agents`, Codex, Gemini CLI, Opencode, OpenSpec, and related agent assets, and those seeded defaults SHALL reflect the current curated workstation skill set from this repository.

#### Scenario: Fresh persisted home receives the repo-managed defaults
- **WHEN** a fresh `/opt/data/home` is prepared for the workstation
- **THEN** the seeded `.agents` and app configuration defaults are created in the persisted home facade
- **AND** those defaults reference the current curated workstation skills from this repository

#### Scenario: Removed curated skills are absent from fresh seed state
- **WHEN** the workstation seeds a fresh persisted home from the repo-managed defaults
- **THEN** the seeded AGENTS guidance and app configuration do not reference removed skills such as `brainstorming`
- **AND** the seeded workstation skill tree does not include removed curated skill payloads

#### Scenario: Runtime does not depend on the host NixOS config tree
- **WHEN** maintainers inspect the seeding inputs
- **THEN** the runtime sources those defaults from repo-managed content in this repository
- **AND** the runtime does not require a host-specific `/home/nixos/nixos-config` path
