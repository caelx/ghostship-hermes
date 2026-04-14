## MODIFIED Requirements

### Requirement: Hermes image ships the GitHub and OpenSSH client CLIs
The workstation contract SHALL document `gh`, `ssh`, `scp`, and `ssh-keygen` as optional userland tools rather than as default seeded image tools, while still giving downstream a supported persisted install path for them.

#### Scenario: Docs describe how optional GitHub and OpenSSH tools persist
- **WHEN** maintainers inspect the runtime docs
- **THEN** the docs explain how downstream can install `gh`, `ssh`, `scp`, and `ssh-keygen` through a supported persisted userland path
- **AND** the docs do not claim those tools are preinstalled by default

### Requirement: Runtime policy documents the GitHub and OpenSSH client CLIs as approved image tools
The repo's runtime policy and operator guidance SHALL describe `gh` and the OpenSSH client tools as approved optional workstation tools, while distinguishing them from the smaller immutable core image tool set.

#### Scenario: Approved extra-CLI policy distinguishes optional userland from immutable core
- **WHEN** maintainers inspect the runtime policy and image guidance
- **THEN** the documented approved optional workstation tool set includes `gh`
- **AND** the documented approved optional workstation tool set includes the OpenSSH client tools needed for `ssh`, `scp`, and `ssh-keygen`
- **AND** that documentation distinguishes optional userland installation from the immutable core image layer
