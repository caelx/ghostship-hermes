## MODIFIED Requirements

### Requirement: Runtime keeps Hermes-native home defaults with a repo-approved whole-home deviation
The workstation runtime SHALL keep `HOME=/home/hermes` and SHALL use `stateDir=/home/hermes`, which makes the managed Hermes state live at `HERMES_HOME=/home/hermes/.hermes`.

#### Scenario: Runtime environment matches the approved contract
- **WHEN** the rebuilt workstation container boots
- **THEN** `HOME` points to `/home/hermes`
- **AND** `HERMES_HOME` points to `/home/hermes/.hermes`

#### Scenario: Terminal access uses the same runtime contract
- **WHEN** an operator opens a runtime shell or browser terminal in the rebuilt image
- **THEN** that session sees the same `HOME=/home/hermes` and `HERMES_HOME=/home/hermes/.hermes` values as the managed Hermes runtime
- **AND** browser terminals start in `/home/hermes`

### Requirement: Runtime documents the whole-home persistence deviation
The workstation SHALL explicitly document that using `/home/hermes` as both the persisted home volume and the Hermes module `stateDir` is a repo-specific deviation from the upstream split-home container-mode layout.

#### Scenario: Deviation is documented
- **WHEN** maintainers inspect the runtime docs
- **THEN** the docs call out the upstream split-home expectation
- **AND** the docs call out the repo-approved `stateDir=/home/hermes` deviation

### Requirement: Systemd runtime preserves the custom dashboard services
The workstation SHALL keep only a minimal Ghostship dashboard stack under the rebuilt runtime.

#### Scenario: Minimal dashboard services come up under the rebuilt runtime
- **WHEN** the rebuilt workstation boots
- **THEN** the browser-facing dashboard service starts successfully
- **AND** the runtime does not require the legacy profile reconciler or per-profile persistent terminal services to make the dashboard available

### Requirement: Hermes-native profiles remain persistent
The workstation SHALL remain compatible with upstream Hermes profile layout.

#### Scenario: Hermes-native profile directories persist under the rebuilt layout
- **WHEN** a user creates Hermes profiles under the rebuilt runtime
- **THEN** the profile directories written through the upstream Hermes layout persist under `~/.hermes/profiles/...`
- **AND** the managed default Hermes state remains at `/home/hermes/.hermes`

#### Scenario: Runtime bootstraps inspection profiles
- **WHEN** the rebuilt image reaches steady state
- **THEN** `test` and `coder` exist under `~/.hermes/profiles/...`
- **AND** operators can inspect the upstream profile layout immediately

## ADDED Requirements

### Requirement: Runtime uses a dedicated hermes identity at UID/GID 3000
If the rebuilt image defines a dedicated `hermes` user, that user SHALL run as UID/GID `3000:3000`.

#### Scenario: Dedicated hermes user resolves to the required numeric identity
- **WHEN** maintainers inspect the rebuilt runtime identity inside the running container
- **THEN** the dedicated `hermes` user resolves to UID `3000`
- **AND** the dedicated `hermes` group resolves to GID `3000`

### Requirement: Runtime SHALL support user-level Nix operations through the persisted daemon socket
The rebuilt runtime SHALL make `nix profile install` available to the `hermes` user when `/nix` is persisted and reused.

#### Scenario: User-level Nix install works in the running container
- **WHEN** the `hermes` user runs `nix profile install`
- **THEN** the install succeeds
- **AND** the resulting binary is usable in the same runtime session
