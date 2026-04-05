## ADDED Requirements

### Requirement: Rebuilt runtime SHALL NOT seed Ghostship-managed workstation content by default
The rebuilt runtime SHALL NOT seed repo-managed workstation app trees, develop-environment defaults, or any custom skill payloads, including Ghostship-managed local skills, into Hermes state or the persisted home facade by default.

#### Scenario: Fresh runtime does not receive Ghostship-managed app/config trees
- **WHEN** a fresh rebuilt runtime boots with empty persisted state
- **THEN** the runtime does not create `.codex`, `.gemini`, `.opencode`, or comparable Ghostship-managed workstation trees as default seeded content
- **AND** the runtime does not populate the persisted home facade with Ghostship-managed app-update systemd units by default

#### Scenario: Fresh runtime does not receive repo-managed custom skill payloads
- **WHEN** a fresh rebuilt runtime boots with empty persisted state
- **THEN** the runtime does not seed repo-managed local Ghostship skills into `~/.hermes/skills`
- **AND** the runtime does not seed vendored Google Workspace skills into `~/.hermes/skills`

## REMOVED Requirements

### Requirement: Workstation seeding targets persisted locations
**Reason**: The rebuilt image is removing the repo-managed workstation seed model rather than relocating it to the new persistence layout.

**Migration**: Runtime docs and tests SHALL stop describing `/data` or `/data/home` as destinations for Ghostship-managed workstation seed trees.

### Requirement: Seeding is copy-if-missing and non-destructive
**Reason**: The removed Ghostship seed model no longer defines the default runtime behavior.

**Migration**: Any remaining compatibility initialization SHALL be documented independently of the old workstation seeding contract.

### Requirement: Seeded workstation defaults mirror the repo-managed develop environment subset
**Reason**: The rebuilt image no longer ships or seeds the repo-managed develop-environment defaults as part of the runtime contract.

**Migration**: Docs, tests, and runtime code SHALL stop assuming the image carries curated Codex/Gemini/Opencode/OpenSpec defaults or repo-managed skill inventories.
