## MODIFIED Requirements

### Requirement: Managed Hermes runtime exposes the approved helper CLI set
The workstation SHALL expose the approved default helper CLI set through persisted userland package-manager layers rather than the immutable image layer. Generic Linux/operator tools SHALL come from the default userland Nix profile, while ecosystem-native tools may come from their native package-manager layer.

#### Scenario: Default helper CLIs come from persisted userland layers
- **WHEN** the workstation has completed its supported first-run userland tool initialization
- **THEN** the approved default helper CLIs are available on the Hermes-user `PATH`
- **AND** those tools resolve from persisted userland package-manager state instead of the immutable image layer

#### Scenario: Missing helper CLI from immutable image is not itself a regression
- **WHEN** maintainers inspect the immutable image layer after this change
- **THEN** the absence of a default helper CLI from the immutable image is not itself a contract failure
- **AND** the contract failure is instead whether the supported default userland layer makes that CLI available as documented

## ADDED Requirements

### Requirement: Generic userland tools default to the persisted Nix layer
The workstation SHALL treat persisted userland Nix as the default package layer for generic Linux/operator tools that are not part of the immutable core runtime.

#### Scenario: Generic tools are installed through the supported Nix layer
- **WHEN** the repo defines the approved default generic tooling set
- **THEN** those tools are provisioned through the persisted Nix layer
- **AND** the docs describe Nix as the supported default package manager for that class of tooling

### Requirement: Node-native agent CLIs default to the persisted npm layer
The workstation SHALL treat npm as the default package manager for Node-native agent CLIs such as `codex`, `gemini-cli`, and `opencode`, and those tools SHALL live in persisted home state rather than the immutable image.

#### Scenario: Node-native agent CLIs resolve from the npm prefix
- **WHEN** the workstation has completed its supported first-run npm tool initialization
- **THEN** supported Node-native agent CLIs resolve from the persisted npm prefix under `/home/hermes`
- **AND** the immutable image does not need to carry those CLIs directly

### Requirement: Repo boot does not continuously overwrite userland tool choices
The workstation SHALL avoid a boot contract that continuously deletes or force-reconciles operator-managed userland tools across every restart.

#### Scenario: User-added tooling survives restart and replacement
- **WHEN** an operator adds supported userland tooling through the persisted Nix or npm layer
- **THEN** that tooling remains present across workstation restarts and container replacement while the same persisted mounts are reused
- **AND** the runtime does not delete it solely because it is not part of the repo’s default seed list
