## MODIFIED Requirements

### Requirement: Managed Hermes runtime exposes the approved helper CLI set
The workstation SHALL expose the approved helper CLI set through the package-manager layer each tool naturally expects, while keeping non-core helper tooling out of the immutable image by default. Native-manager installs SHALL be preferred where they are the upstream-supported path, and persisted Nix SHALL remain available as an optional fallback layer for downstream or Hermes-installed extras. The image-managed baseline Nix helper set SHALL resolve through the reconciled managed Nix default profile rather than through raw build-time `/nix/store/...` symlinks.

#### Scenario: Shipped helper CLIs come from their expected package-manager layers
- **WHEN** the workstation has completed its supported first-run initialization
- **THEN** the approved shipped helper CLIs are available on the Hermes-user `PATH`
- **AND** those tools resolve from their documented package-manager layers instead of from a repo-owned convergence shim
- **AND** baseline Nix-backed defaults resolve from the managed Nix default profile that the boot runtime reconciles into persisted `/nix`

#### Scenario: Missing helper CLI from immutable image is not itself a regression
- **WHEN** maintainers inspect the immutable image layer after this change
- **THEN** the absence of a non-core helper CLI from the immutable image is not itself a contract failure
- **AND** the contract failure is instead whether the tool is available through its documented install path

## ADDED Requirements

### Requirement: Runtime validation proves managed Nix helper defaults survive reused `/nix`
The workstation validation suite SHALL prove that guaranteed Nix-backed helper tools remain callable when a container restarts or is replaced while reusing an existing non-empty persisted `/nix`.

#### Scenario: Smoke validation exercises baseline managed Nix tools after replacement
- **WHEN** maintainers run the workstation image validation suite against a reused persisted `/nix`
- **THEN** the suite executes representative baseline helper commands such as `bw`, `gws`, `gh`, `gcloud`, and `blogtato`
- **AND** the suite fails if those commands are present only as broken symlinks to missing `/nix/store/...` paths
