## MODIFIED Requirements

### Requirement: Normal invocation uses local installed state
The workstation SHALL run Hermes from the image-owned runtime under `/opt/hermes` while resolving operator-installed userland tools from persisted package-manager state under `/nix` and `/home/hermes`, and Hermes terminal execution SHALL default to the local container backend instead of a nested Docker sandbox.

#### Scenario: Hermes resolves from the immutable core runtime
- **WHEN** an operator or service invokes `hermes` inside the workstation container
- **THEN** the resolved executable comes from the image-owned Hermes core runtime under `/opt/hermes`
- **AND** the invocation does not depend on a persisted managed Nix profile entry shadowing the current image generation

#### Scenario: Userland tools resolve from persisted package-manager layers
- **WHEN** an operator or Hermes session invokes a supported userland tool from the workstation `PATH`
- **THEN** tools may resolve from their documented persisted package-manager layers
- **AND** Node-native agent CLIs may resolve from the persisted npm prefix under `/home/hermes`
- **AND** the runtime does not require a live network refresh in the hot path of that invocation

#### Scenario: Hermes terminal execution stays local to the workstation container
- **WHEN** the managed Hermes runtime executes terminal work with its default terminal backend
- **THEN** the execution runs directly inside the workstation container
- **AND** the runtime does not require the nested Docker terminal backend for the supported default path

### Requirement: Runtime keeps only a minimum viable immutable system layer
The workstation SHALL keep only the minimum immutable image layer needed for Ubuntu boot, `s6` supervision, Hermes core, the mandatory router and dashboard surfaces, `ttyd`, Nix, Node/npm, and the small set of shell/process/network utilities directly required by core runtime functions.

#### Scenario: Immutable core excludes convenience tooling without a core call site
- **WHEN** maintainers inspect the immutable image contents after this change
- **THEN** convenience CLIs such as `jq`, `fd`, `gh`, `gcloud`, `gws`, `bws`, `uv`, and `yq` are not kept in the immutable layer unless a documented core boot/runtime call site requires them
- **AND** those tools instead belong to optional persisted userland layers

#### Scenario: Immutable core keeps required package-manager/runtime surfaces
- **WHEN** maintainers inspect the immutable image contents after this change
- **THEN** the image retains Nix because it is the supported optional userland package manager
- **AND** the image retains Node/npm because npm is the supported native package manager for Node-native agent CLIs

## REMOVED Requirements

### Requirement: Managed gateway commands align with upstream Hermes user services
**Reason**: The new workstation image keeps Hermes config and state host-native, but it moves container service supervision to `s6` plus Docker instead of `systemd --user`.
**Migration**: Operators SHALL manage Hermes config through the CLI, dashboard, and files under persisted home state, while the long-running gateway/dashboard/router process lifecycle is managed through `s6` service wiring and Docker restart policy instead of `hermes gateway install`.

## ADDED Requirements

### Requirement: Workstation image uses Ubuntu 24.04 with `s6` supervision
The workstation SHALL use `ubuntu:24.04` as its base OS and SHALL supervise its mandatory long-running services through `s6` inside the container.

#### Scenario: Maintainer inspects the base runtime contract
- **WHEN** maintainers inspect the workstation image build or runtime contract
- **THEN** the base OS is Ubuntu 24.04
- **AND** the container PID 1 path uses `s6`

### Requirement: Mandatory workstation services are supervised in-container
The workstation SHALL treat the published web listener, Hermes gateway, Hermes dashboard, Ghostship router, and the `ttyd` terminal sidecar as mandatory long-running in-container services under the supervision layer.

#### Scenario: Core product services start under supervision
- **WHEN** the workstation container starts successfully
- **THEN** `s6` starts and supervises the published web listener service
- **AND** `s6` starts and supervises the Hermes gateway service
- **AND** `s6` starts and supervises the Hermes dashboard service
- **AND** `s6` starts and supervises the Ghostship router service
- **AND** `s6` starts and supervises the `ttyd` terminal sidecar service

### Requirement: Hermes core is immutable and image-owned
The workstation SHALL keep Hermes core in an immutable image-owned path so image replacement upgrades Hermes itself without requiring the persisted home layer to own the runtime checkout.

#### Scenario: Image replacement updates Hermes core without replacing home state
- **WHEN** the operator replaces the container image while reusing the same persisted `/home/hermes`
- **THEN** the Hermes runtime used by the container comes from the new image’s `/opt/hermes`
- **AND** the persisted home state remains intact across that replacement
