## ADDED Requirements

### Requirement: Repo vendors the upstream Google Workspace skill catalog
The repo SHALL store a committed snapshot of the upstream Google Workspace skill catalog so image builds and runtime skill seeding do not depend on live network fetches.

#### Scenario: Vendored snapshot is present in the repo
- **WHEN** maintainers inspect the repository contents for the Google Workspace integration
- **THEN** the upstream `gws-*`, persona, and recipe skill directories are present as committed files in a repo-managed vendor location
- **AND** the snapshot corresponds to the same upstream revision used for the packaged `gws` CLI

### Requirement: Runtime seeds vendored Google Workspace skills without overwriting user content
The Hermes runtime SHALL copy vendored Google Workspace skills into `~/.hermes/skills` on first start only when the destination skill directory does not already exist.

#### Scenario: Missing vendored skill is seeded
- **WHEN** a vendored Google Workspace skill directory is absent from `~/.hermes/skills`
- **THEN** runtime skill seeding copies that skill into the Hermes profile

#### Scenario: Existing skill directory is preserved
- **WHEN** a skill directory with the same name already exists in `~/.hermes/skills`
- **THEN** runtime skill seeding leaves the existing directory unchanged
- **AND** the seeding flow does not overwrite user-managed content

### Requirement: Repo-managed local skills remain available alongside vendored skills
The default skill inventory SHALL continue to include repo-managed local skills together with the vendored Google Workspace skills.

#### Scenario: Seeded inventory contains both local and upstream skills
- **WHEN** a fresh Hermes profile receives default skills
- **THEN** the seeded inventory includes repo-managed local skills such as runtime/container guidance skills
- **AND** it also includes the vendored Google Workspace skills in the same default skill tree
