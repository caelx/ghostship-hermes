## ADDED Requirements

### Requirement: Workstation mirrors selected develop-environment defaults
The workstation SHALL seed a repo-managed mirror of the selected develop-environment defaults into `/home/hermes`, including the shared `.agents` tree and agent app configuration defaults needed for Codex, Gemini CLI, Opencode, and OpenSpec.

#### Scenario: Fresh workstation receives develop defaults
- **WHEN** a fresh persisted home is prepared for the workstation
- **THEN** the boot seeding flow creates the repo-managed default `.agents` and app config content in `/home/hermes`

#### Scenario: Seed content comes from repo-managed sources
- **WHEN** maintainers inspect the workstation bootstrap inputs
- **THEN** the mirrored develop-environment defaults are sourced from repo-managed content in this repository
- **AND** the runtime does not depend on a host-specific `/home/nixos/nixos-config` path

### Requirement: Workstation seeding distinguishes managed defaults from user-owned state
The workstation SHALL document which seeded files remain managed by the image/bootstrap process and which become user-owned after their first creation.

#### Scenario: Docs identify managed versus user-owned paths
- **WHEN** maintainers inspect the workstation seeding docs
- **THEN** the docs explain how seeded defaults interact with later local edits
- **AND** the docs identify any paths that remain managed and replaceable during future seed refreshes
