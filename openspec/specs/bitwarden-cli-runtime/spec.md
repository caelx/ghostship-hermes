# bitwarden-cli-runtime Specification

## Purpose
TBD - created by archiving change add-bitwarden-cli-runtime-and-skill. Update Purpose after archive.
## Requirements
### Requirement: Hermes image ships the official Bitwarden CLI
The Hermes image SHALL include the official `bw` Bitwarden CLI on `PATH`, and the executable SHALL come from the repo's normal Nix/image package wiring rather than an ad hoc runtime installer.

#### Scenario: Image build exposes `bw`
- **WHEN** the Hermes image is built from the repo flake
- **THEN** the image contents include the `bw` executable
- **AND** the executable is available on `PATH` inside the container runtime

#### Scenario: Repo evaluation covers the Bitwarden CLI package
- **WHEN** maintainers run the repo's normal flake evaluation or inspect package outputs
- **THEN** the Bitwarden CLI package wiring evaluates successfully
- **AND** the Hermes image package depends on that evaluated package path

### Requirement: Hermes runtime supports a documented Bitwarden appdata location
The Hermes runtime and docs SHALL provide a stable, user-writable convention for `BITWARDENCLI_APPDATA_DIR` so the official Bitwarden CLI can keep its local state under Hermes-managed persistent storage.

#### Scenario: Recommended appdata path lives under Hermes-managed state
- **WHEN** maintainers inspect the Bitwarden integration docs and runtime conventions
- **THEN** the recommended `BITWARDENCLI_APPDATA_DIR` points to a writable location under the Hermes home or profile state
- **AND** the location is compatible with persisted Hermes runtime data across container restarts

