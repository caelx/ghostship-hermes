## MODIFIED Requirements

### Requirement: Runtime keeps Hermes-native environment defaults
The workstation runtime SHALL align with upstream Hermes container-mode expectations by keeping `HERMES_HOME=/data/.hermes` and `HOME=/home/hermes`.

#### Scenario: Runtime environment matches the upstream Hermes container contract
- **WHEN** the rebuilt workstation container boots
- **THEN** `HERMES_HOME` points to `/data/.hermes`
- **AND** `HOME` points to `/home/hermes`

#### Scenario: Terminal access uses the same runtime contract
- **WHEN** an operator opens a runtime shell or browser terminal in the rebuilt image
- **THEN** that session sees the same `HERMES_HOME=/data/.hermes` and `HOME=/home/hermes` values as the managed Hermes runtime

### Requirement: Runtime SHALL keep `HERMES_HOME` isolated from the HOME persistence facade
The workstation SHALL keep upstream Hermes state under `/data/.hermes` without merging it into `/data/home` or shadowing it through `/home/hermes`.

#### Scenario: Hermes state root remains canonical
- **WHEN** maintainers inspect the rebuilt runtime layout
- **THEN** Hermes state lives under `/data/.hermes`
- **AND** the HOME persistence facade under `/data/home` does not replace or contain the canonical `HERMES_HOME` root

#### Scenario: Home facade does not interfere with Hermes-managed state
- **WHEN** Hermes reads or writes profile state, config, sessions, memories, or other `HERMES_HOME` content
- **THEN** those operations resolve against `/data/.hermes`
- **AND** the runtime does not redirect them through general HOME-backed symlinks

### Requirement: Runtime repairs the persisted home facade before starting user services
The workstation SHALL create and repair the managed symlinks from `/home/hermes` into `/data/home` before starting any HOME-anchored user service or browser terminal flow.

#### Scenario: Managed home facade is ready before user-facing processes start
- **WHEN** the rebuilt runtime prepares the user environment
- **THEN** the managed home symlinks already resolve into `/data/home`
- **AND** HOME-anchored state is available through the facade before user-facing processes start

### Requirement: Systemd runtime preserves the custom dashboard services
The workstation SHALL keep only a minimal Ghostship dashboard stack under the rebuilt runtime, and that stack SHALL provide browser access without the current profile-reconciler architecture.

#### Scenario: Minimal dashboard services come up under the rebuilt runtime
- **WHEN** the rebuilt workstation boots
- **THEN** the browser-facing dashboard service starts successfully
- **AND** the runtime does not require the legacy profile reconciler or per-profile persistent terminal services to make the dashboard available

### Requirement: Hermes-native profiles and gateway install remain persistent
The workstation SHALL remain compatible with upstream Hermes profile layout and gateway install behavior without adding Ghostship-managed profile orchestration.

#### Scenario: Hermes-native profile directories persist under the rebuilt layout
- **WHEN** a user creates Hermes profiles under the rebuilt runtime
- **THEN** the profile directories written through the upstream Hermes layout persist under `~/.hermes/profiles/...` through the `/data/home` facade
- **AND** the canonical managed `HERMES_HOME` remains `/data/.hermes`
- **AND** the runtime does not require a separate Ghostship profile registry to keep those profiles available

#### Scenario: HOME-anchored gateway units remain persistent
- **WHEN** Hermes installs a user gateway unit into `~/.config/systemd/user`
- **THEN** the installed unit persists through the managed `/data/home` facade
- **AND** the runtime does not require a Ghostship-managed compatibility copier to preserve that user-owned unit

### Requirement: Normal invocation uses local installed state
The workstation SHALL use the upstream Hermes package, persisted Hermes state, and current user-level runtime state during normal invocation rather than Ghostship-managed app bootstrap or refresh flows.

#### Scenario: Normal invocation does not depend on Ghostship-managed app refresh
- **WHEN** Hermes commands or retained runtime tools are invoked in the rebuilt image
- **THEN** the invocation uses the currently installed local runtime state
- **AND** the invocation does not first depend on Ghostship-managed Codex, Gemini CLI, Opencode, OpenSpec, or `skills` update flows

## ADDED Requirements

### Requirement: Runtime uses a dedicated hermes identity at UID/GID 3000 when the image defines that user
If the rebuilt image defines a dedicated `hermes` user, that user SHALL run as UID/GID `3000:3000`.

#### Scenario: Dedicated hermes user resolves to the required numeric identity
- **WHEN** maintainers inspect the rebuilt runtime identity inside the running container
- **THEN** the dedicated `hermes` user resolves to UID `3000`
- **AND** the dedicated `hermes` group resolves to GID `3000`

#### Scenario: Persisted volumes remain writable to the dedicated runtime identity
- **WHEN** the rebuilt image starts with reused persisted state mounts
- **THEN** the runtime `hermes` identity can read and write the supported persisted paths without a Ghostship-specific identity rewrite layer

### Requirement: Runtime SHALL support user-level Nix operations through the persisted daemon socket
The rebuilt runtime SHALL make `nix profile install` available to the `hermes` user when `/nix` is persisted and reused.

#### Scenario: Nix daemon socket is active in the running container
- **WHEN** the rebuilt container reaches its steady state
- **THEN** `nix-daemon.socket` is active
- **AND** the runtime exposes a working `/nix/var/nix/daemon-socket/socket`

#### Scenario: User-level Nix install works in the running container
- **WHEN** the `hermes` user runs `nix profile install`
- **THEN** the install succeeds without additional image-side bootstrap
- **AND** the resulting binary is usable in the same runtime session

## REMOVED Requirements

### Requirement: Runtime does not install or require sudo
**Reason**: The rebuilt image is aligning with upstream Hermes container-mode behavior rather than preserving the repo's previous no-sudo runtime contract.

**Migration**: Runtime docs and tests SHALL stop asserting the absence of `sudo` as part of the image contract.
