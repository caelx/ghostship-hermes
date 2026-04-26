## MODIFIED Requirements

### Requirement: Hermes image ships the official Bitwarden CLI
The workstation contract SHALL ship and document the official `bw` Bitwarden Password Manager CLI as an image-managed userland tool.

#### Scenario: Image includes `bw`
- **WHEN** maintainers inspect the runtime docs
- **THEN** the docs describe `bw` as preinstalled by default
- **AND** validation checks that `bw --help` runs in the image

### Requirement: Hermes image ships Bitwarden session wrappers
The workstation contract SHALL ship `bw-unlock` and `bw-lock` as image-managed wrapper commands for the normal Bitwarden CLI session workflow.

#### Scenario: Image includes Bitwarden wrappers
- **WHEN** maintainers inspect the runtime docs and validation checks
- **THEN** the docs describe `bw-unlock` and `bw-lock` as preinstalled by default
- **AND** validation checks that both wrapper help commands run in the image

#### Scenario: Lock preserves authenticated account state
- **WHEN** `bw-lock` is used
- **THEN** it removes the active runtime `BW_SESSION`
- **AND** it does not log out of the persisted Bitwarden account

### Requirement: Hermes runtime supports a documented Bitwarden appdata location
The Hermes runtime and docs SHALL provide a stable, user-writable convention for `bw` local configuration/state under persisted Hermes home storage, rather than relying on default host-oriented XDG paths.

#### Scenario: Recommended config path lives under persisted home state
- **WHEN** maintainers inspect the Bitwarden integration docs and runtime conventions
- **THEN** the recommended `BITWARDENCLI_APPDATA_DIR` points to `/home/hermes/.local/state/bitwarden-cli`
- **AND** the location is compatible with persisted workstation state across container restarts and replacement
- **AND** the runtime `BW_SESSION` file is under `/run/user/3000/ghostship-bitwarden/session.env`
