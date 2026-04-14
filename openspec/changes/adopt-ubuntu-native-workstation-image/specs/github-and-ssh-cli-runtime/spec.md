## MODIFIED Requirements

### Requirement: Hermes image ships the GitHub and OpenSSH client CLIs
The default workstation contract SHALL make `gh`, `ssh`, `scp`, and `ssh-keygen` available on `PATH` through the repo’s default persisted userland Nix layer rather than requiring those executables to live in the immutable core image.

#### Scenario: Default workstation exposes `gh`, `ssh`, `scp`, and `ssh-keygen`
- **WHEN** the workstation has completed its supported default userland Nix initialization
- **THEN** the runtime exposes the `gh` executable
- **AND** the runtime exposes the `ssh`, `scp`, and `ssh-keygen` executables
- **AND** those executables are available on `PATH` inside the container runtime without an additional manual installation step

### Requirement: Runtime policy documents the GitHub and OpenSSH client CLIs as approved image tools
The repo's runtime policy and operator guidance SHALL describe `gh` and the OpenSSH client tools as approved default workstation tools, while distinguishing them from the smaller immutable core image tool set.

#### Scenario: Approved extra-CLI policy distinguishes default userland from immutable core
- **WHEN** maintainers inspect the runtime policy and image guidance
- **THEN** the documented approved default workstation tool set includes `gh`
- **AND** the documented approved default workstation tool set includes the OpenSSH client tools needed for `ssh`, `scp`, and `ssh-keygen`
- **AND** that documentation distinguishes the default userland tool layer from the immutable core image layer
