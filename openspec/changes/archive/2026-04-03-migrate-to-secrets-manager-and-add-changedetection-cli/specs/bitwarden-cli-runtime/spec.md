## MODIFIED Requirements

### Requirement: Hermes image ships the official Bitwarden CLI
The Hermes image SHALL include the official `bws` Bitwarden Secrets Manager CLI on `PATH`, and the executable SHALL come from the repo's normal Nix/image package wiring rather than an ad hoc runtime installer.

#### Scenario: Image build exposes `bws`
- **WHEN** the Hermes image is built from the repo flake
- **THEN** the image contents include the `bws` executable
- **AND** the executable is available on `PATH` inside the container runtime

#### Scenario: Repo evaluation covers the Bitwarden CLI package
- **WHEN** maintainers run the repo's normal flake evaluation or inspect package outputs
- **THEN** the Bitwarden Secrets Manager CLI package wiring evaluates successfully
- **AND** the Hermes image package depends on that evaluated package path

### Requirement: Hermes runtime supports a documented Bitwarden appdata location
The Hermes runtime and docs SHALL provide a stable, user-writable convention for `bws` local configuration/state under Hermes-managed persistent storage, rather than relying on default host-oriented XDG paths.

#### Scenario: Recommended config path lives under Hermes-managed state
- **WHEN** maintainers inspect the Bitwarden integration docs and runtime conventions
- **THEN** the recommended `bws` configuration/state path points to a writable location under the Hermes home or profile state
- **AND** the location is compatible with persisted Hermes runtime data across container restarts

#### Scenario: Runtime prepares the Bitwarden state path
- **WHEN** the Hermes runtime initializes a profile
- **THEN** it creates the documented `bws` parent directory under Hermes-managed storage
- **AND** the resulting path is writable by the Hermes runtime user
