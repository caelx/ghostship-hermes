## MODIFIED Requirements

### Requirement: Hermes image ships the official Bitwarden CLI
The workstation contract SHALL document the official `bws` Bitwarden Secrets Manager CLI as an optional userland tool rather than as a default seeded image tool, while still giving downstream a supported persisted install path for it.

#### Scenario: Docs describe how optional `bws` persists
- **WHEN** maintainers inspect the runtime docs
- **THEN** the docs explain how downstream can install `bws` through a supported persisted userland path
- **AND** the docs do not claim `bws` is preinstalled by default

### Requirement: Hermes runtime supports a documented Bitwarden appdata location
The Hermes runtime and docs SHALL provide a stable, user-writable convention for `bws` local configuration/state under persisted Hermes home storage, rather than relying on default host-oriented XDG paths.

#### Scenario: Recommended config path lives under persisted home state
- **WHEN** maintainers inspect the Bitwarden integration docs and runtime conventions
- **THEN** the recommended `bws` configuration/state path points to a writable location under `/home/hermes`
- **AND** the location is compatible with persisted workstation state across container restarts and replacement
