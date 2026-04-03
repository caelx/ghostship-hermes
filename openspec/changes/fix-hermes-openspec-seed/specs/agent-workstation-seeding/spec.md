## MODIFIED Requirements

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
