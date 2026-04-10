## ADDED Requirements

### Requirement: Hermes image ships the GitHub and OpenSSH client CLIs
The default Hermes image SHALL include `gh`, `ssh`, and `scp` on PATH, and those executables SHALL come from the repo's normal Nix/image package wiring rather than an ad hoc runtime installer.

#### Scenario: Default image exposes `gh`, `ssh`, and `scp`
- **WHEN** the default Hermes image is built from the repo flake
- **THEN** the image contents include the `gh` executable
- **AND** the image contents include the `ssh` and `scp` executables
- **AND** those executables are available on PATH inside the container runtime without an additional installation step

### Requirement: Repo evaluation covers the GitHub and OpenSSH client packages
The repo flake SHALL evaluate the `gh` and OpenSSH client integration as part of normal package and image wiring so integration failures appear during standard flake checks, derivation inspection, or image build workflows.

#### Scenario: Flake evaluation includes the GitHub and OpenSSH client package wiring
- **WHEN** maintainers run the repo's flake checks or inspect package outputs
- **THEN** the `gh` and OpenSSH client package wiring evaluates successfully as part of the repo flake outputs
- **AND** the default Hermes image package depends on that evaluated package path

### Requirement: Runtime policy documents the GitHub and OpenSSH client CLIs as approved image tools
The repo's runtime policy and operator guidance SHALL describe `gh` and the OpenSSH client tools as approved non-`ghostship-*` CLIs in the default image.

#### Scenario: Approved extra-CLI policy includes `gh` and OpenSSH client tools
- **WHEN** maintainers inspect the runtime policy and image guidance
- **THEN** the documented approved non-`ghostship-*` CLI set includes `gh`
- **AND** the documented approved non-`ghostship-*` CLI set includes the OpenSSH client tools needed for `ssh` and `scp`
- **AND** that documentation aligns with the image package wiring that exposes those executables on PATH
