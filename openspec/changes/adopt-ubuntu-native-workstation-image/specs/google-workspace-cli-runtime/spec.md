## MODIFIED Requirements

### Requirement: Hermes image ships a pinned Google Workspace CLI
The default workstation contract SHALL make the upstream `gws` executable available on `PATH` through the repo’s default persisted userland Nix layer, and the executable SHALL remain sourced from a pinned upstream revision rather than an ad hoc runtime download.

#### Scenario: Default workstation exposes `gws`
- **WHEN** the workstation has completed its supported default userland Nix initialization
- **THEN** the runtime exposes the `gws` executable
- **AND** the executable is available on `PATH` inside the container runtime without an additional manual installation step

#### Scenario: Upstream revision remains pinned in repo wiring
- **WHEN** maintainers inspect the repo package wiring for the default `gws` tool
- **THEN** the `gws` package source resolves from a pinned upstream revision
- **AND** the default workstation contract does not depend on an ad hoc runtime download to provide it

### Requirement: Image contract remains package-based
The workstation SHALL include `gws` through the repo-managed default userland package set rather than through a separate skill bundle or a mutable ad hoc installer.

#### Scenario: Maintainer inspects the default tool composition
- **WHEN** maintainers inspect the default workstation tool composition logic
- **THEN** `gws` is included through the repo-managed default userland package set
- **AND** the integration does not depend on a separate Google Workspace skill bundle
