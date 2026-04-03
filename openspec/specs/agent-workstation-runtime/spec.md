## ADDED Requirements

### Requirement: Runtime keeps Hermes-native environment defaults
The workstation runtime SHALL keep `HERMES_HOME=/opt/data` and `HOME=/home/hermes` so Hermes runs with its upstream Docker state root while the workstation still has a normal user home.

#### Scenario: Runtime environment matches the Hermes-native contract
- **WHEN** the workstation container boots
- **THEN** `HERMES_HOME` points to `/opt/data`
- **AND** `HOME` points to `/home/hermes`

### Requirement: Runtime repairs the persisted home facade before starting user services
The workstation SHALL create and repair the managed symlinks from `/home/hermes` into `/opt/data/home` before starting the `hermes` user manager or any HOME-anchored user service.

#### Scenario: Managed home facade is ready before systemd user units start
- **WHEN** the workstation runtime prepares the user environment
- **THEN** the managed home symlinks already resolve into `/opt/data/home`
- **AND** `~/.config/systemd/user` persists through the symlinked home facade

### Requirement: Systemd runtime preserves the custom dashboard services
The workstation SHALL continue to run the custom Ghostship Hermes dashboard stack under the `systemd` runtime after the persistence-layout change.

#### Scenario: Dashboard services still come up under systemd
- **WHEN** the workstation boots under the new persistence model
- **THEN** the system-level dashboard services still start under `systemd`
- **AND** the browser-facing dashboard remains available through the supported runtime path

### Requirement: Hermes-native profiles and gateway install remain persistent
The workstation SHALL preserve Hermes-native named profile behavior, wrapper paths, and `gateway install` behavior under the new persistence layout.

#### Scenario: Named profiles persist through the home facade
- **WHEN** a user creates named Hermes profiles
- **THEN** the profile directories written through `Path.home() / ".hermes" / "profiles"` persist through the managed home facade

#### Scenario: User gateway units persist through the home facade
- **WHEN** Hermes installs a user gateway service into `~/.config/systemd/user`
- **THEN** the installed unit persists across container rebuilds and restarts through `/opt/data/home/.config/systemd/user`

### Requirement: Runtime does not install or require sudo
The workstation SHALL continue to run without general in-container `sudo`.

#### Scenario: Runtime image omits sudo
- **WHEN** maintainers inspect the workstation image contents and runtime docs
- **THEN** the image does not rely on a general-purpose `sudo` package for normal operation
- **AND** the documented runtime workflows do not require `sudo` inside the container

### Requirement: Normal invocation uses local installed state
The workstation SHALL use already-installed local apps and persisted local state during normal invocation rather than requiring live network refresh in the hot path.

#### Scenario: Local invocation does not wait for refresh
- **WHEN** the agent invokes `codex`, `gemini-cli`, `opencode`, `openspec`, `skills`, or Hermes commands
- **THEN** the invocation uses the currently installed local workstation state
- **AND** the invocation does not first require a live update round trip
