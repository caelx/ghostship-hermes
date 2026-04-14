## MODIFIED Requirements

### Requirement: Hermes image ships a pinned Google Workspace CLI
The workstation contract SHALL treat the upstream `gws` executable as an optional userland tool rather than as a default seeded image tool, and any documented install path SHALL remain sourced from a pinned upstream revision rather than an ad hoc runtime download.

#### Scenario: Docs describe how optional `gws` persists
- **WHEN** maintainers inspect the runtime docs
- **THEN** the docs explain how downstream can install `gws` through a supported persisted userland path
- **AND** the docs do not claim `gws` is preinstalled by default

#### Scenario: Upstream revision remains pinned in repo wiring
- **WHEN** maintainers inspect the repo package wiring for the default `gws` tool
- **THEN** the `gws` package source resolves from a pinned upstream revision
- **AND** the default workstation contract does not depend on an ad hoc runtime download to provide it

### Requirement: Image contract remains package-based
The workstation SHALL document `gws` through a pinned package-based install path rather than through a separate skill bundle or a mutable ad hoc installer.

#### Scenario: Maintainer inspects the optional tool composition
- **WHEN** maintainers inspect the optional workstation tool composition logic
- **THEN** `gws` is included through a pinned documented userland package path
- **AND** the integration does not depend on a separate Google Workspace skill bundle
