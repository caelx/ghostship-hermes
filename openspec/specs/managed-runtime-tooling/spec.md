## MODIFIED Requirements

### Requirement: Managed Hermes runtime exposes the approved helper CLI set
The workstation SHALL expose the approved helper CLI set through the package-manager layer each tool naturally expects, while keeping non-core helper tooling out of the immutable image by default. Native-manager installs SHALL be preferred where they are the upstream-supported path, and persisted Nix SHALL remain available as an optional fallback layer for downstream or Hermes-installed extras.

#### Scenario: Shipped helper CLIs come from their expected package-manager layers
- **WHEN** the workstation has completed its supported first-run initialization
- **THEN** the approved shipped helper CLIs are available on the Hermes-user `PATH`
- **AND** those tools resolve from their documented package-manager layers instead of from a repo-owned convergence shim

#### Scenario: Missing helper CLI from immutable image is not itself a regression
- **WHEN** maintainers inspect the immutable image layer after this change
- **THEN** the absence of a non-core helper CLI from the immutable image is not itself a contract failure
- **AND** the contract failure is instead whether the tool is available through its documented install path

## ADDED Requirements

### Requirement: Persisted Nix remains available as an optional userland layer
The workstation SHALL keep persisted Nix available for downstream or Hermes-installed userland tooling that should survive container replacement, without requiring the image to preseed a large default Nix utility profile.

#### Scenario: Optional Nix installs survive replacement
- **WHEN** an operator or Hermes installs extra tooling through persisted Nix
- **THEN** that tooling remains available while the same `/nix` mount is reused
- **AND** the docs describe persisted Nix as an optional supported package layer rather than the default answer for every extra CLI

### Requirement: Node-native agent CLIs default to the persisted npm layer
The workstation SHALL treat npm as the default package manager for Node-native agent CLIs such as `codex`, `gemini-cli`, `agent-browser`, and `opencode`, and those tools SHALL live in persisted home state rather than the immutable image.

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
