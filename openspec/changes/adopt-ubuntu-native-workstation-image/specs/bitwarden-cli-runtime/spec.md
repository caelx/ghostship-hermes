## MODIFIED Requirements

### Requirement: Hermes image ships the official Bitwarden CLI
The default workstation contract SHALL make the official `bws` Bitwarden Secrets Manager CLI available on `PATH` through the repo’s default persisted userland Nix layer rather than requiring the executable to live in the immutable core image.

#### Scenario: Workstation runtime exposes `bws`
- **WHEN** the workstation has completed its supported default userland Nix initialization
- **THEN** the runtime exposes the `bws` executable
- **AND** the executable is available on `PATH` inside the container runtime

### Requirement: Hermes runtime supports a documented Bitwarden appdata location
The Hermes runtime and docs SHALL provide a stable, user-writable convention for `bws` local configuration/state under persisted Hermes home storage, rather than relying on default host-oriented XDG paths.

#### Scenario: Recommended config path lives under persisted home state
- **WHEN** maintainers inspect the Bitwarden integration docs and runtime conventions
- **THEN** the recommended `bws` configuration/state path points to a writable location under `/home/hermes`
- **AND** the location is compatible with persisted workstation state across container restarts and replacement
