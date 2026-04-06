## REMOVED Requirements

### Requirement: Repo vendors the upstream Google Workspace skill catalog
**Reason**: The active Google Workspace integration is being narrowed to the packaged `gws` CLI only, and the repo should not carry a committed upstream skill snapshot for the default image/runtime.
**Migration**: Use the packaged `gws` executable directly after authenticating it. Do not expect a repo-vendored Google Workspace skill catalog in the image or repository.

### Requirement: Runtime seeds vendored Google Workspace skills without overwriting user content
**Reason**: The default Hermes runtime should not seed Google Workspace skills at first start because Google Workspace skills are out of scope for the image.
**Migration**: Remove any implementation plans that copy Google Workspace skills into `~/.hermes/skills`; the runtime should leave that directory untouched by this integration.

### Requirement: Repo-managed local skills remain available alongside vendored skills
**Reason**: The repo is no longer treating Google Workspace skills as part of the default skill inventory, so there is no combined local-plus-vendored Google Workspace skill tree to preserve.
**Migration**: Keep repo-managed local skills separate from Google Workspace support and treat `gws` availability as a CLI-only concern.

## ADDED Requirements

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
