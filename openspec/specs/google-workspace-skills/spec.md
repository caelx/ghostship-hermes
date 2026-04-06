# google-workspace-skills Specification

## Purpose
TBD - created by archiving change add-google-workspace-cli-and-vendor-skills. Update Purpose after archive.
## Requirements
### Requirement: Default image excludes Google Workspace skill bundles
The default Hermes image and repository SHALL NOT vendor, commit, or otherwise depend on a Google Workspace skill catalog to provide Google Workspace support.

#### Scenario: Repository contents stay CLI-only
- **WHEN** maintainers inspect the repository contents for the Google Workspace integration
- **THEN** there is no repo-managed vendor snapshot of upstream Google Workspace skills required by the default image
- **AND** Google Workspace support is represented by the packaged `gws` CLI contract instead

### Requirement: Runtime does not seed Google Workspace skills
The Hermes runtime SHALL NOT copy Google Workspace skill directories into `~/.hermes/skills` or another default runtime skill tree as part of image bootstrap or first-start setup.

#### Scenario: Fresh runtime does not add Google Workspace skills
- **WHEN** a fresh Hermes profile starts from the default image
- **THEN** the runtime does not create Google Workspace skill directories as part of bootstrap
- **AND** Google Workspace support remains limited to the `gws` executable on `PATH`

### Requirement: Default skill inventory remains repo-specific
The default skill inventory SHALL remain limited to repo-managed local skills and SHALL NOT imply that Google Workspace skills are bundled by default.

#### Scenario: Default skills do not include Google Workspace content
- **WHEN** maintainers inspect the default runtime skill tree and related documentation
- **THEN** repo-managed local skills may still be present according to repo policy
- **AND** Google Workspace skills are not described or shipped as part of that default inventory
