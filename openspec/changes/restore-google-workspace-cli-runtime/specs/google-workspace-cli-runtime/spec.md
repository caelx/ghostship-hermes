## MODIFIED Requirements

### Requirement: Hermes image ships a pinned Google Workspace CLI
The default Hermes image SHALL include the upstream `gws` executable on `PATH`, and the executable SHALL be built from a pinned flake input revision rather than installed through an ad hoc runtime package manager flow.

#### Scenario: Default image exposes `gws`
- **WHEN** the default Hermes image is built from the repo flake
- **THEN** the image contents include the `gws` executable
- **AND** the executable is available on `PATH` inside the container runtime without an additional installation step

#### Scenario: Upstream revision is pinned in flake wiring
- **WHEN** maintainers inspect the repo flake and package wiring
- **THEN** the `gws` package source resolves from a pinned upstream flake input
- **AND** the image does not rely on `npm install -g`, release-tarball download steps, or runtime bootstrap installs to provide `gws`

### Requirement: Repo evaluation covers the Google Workspace CLI package
The repo flake SHALL evaluate the `gws` integration as part of normal package and image wiring so integration failures appear during standard flake checks, derivation inspection, or image build workflows.

#### Scenario: Flake evaluation includes `gws`
- **WHEN** maintainers run the repo's flake checks or inspect package outputs
- **THEN** the `gws` package wiring evaluates successfully as part of the repo flake outputs
- **AND** the default Hermes image package depends on that evaluated package

#### Scenario: Image contract remains package-based
- **WHEN** maintainers inspect the image composition logic
- **THEN** `gws` is included through the repo-managed package set that projects tools onto the runtime `PATH`
- **AND** the integration does not depend on a separate Google Workspace skill bundle
