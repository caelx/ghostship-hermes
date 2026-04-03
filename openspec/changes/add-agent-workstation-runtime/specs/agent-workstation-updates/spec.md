## ADDED Requirements

### Requirement: Agent apps update automatically on boot and on timers
The workstation SHALL install and update `codex`, `gemini-cli`, `opencode`, `openspec`, and `skills` automatically at boot and through scheduled refresh services without requiring manual intervention.

#### Scenario: Boot update converges app installs
- **WHEN** the workstation boots
- **THEN** the boot update flow checks and updates the managed agent apps
- **AND** the workstation keeps using the previous local version if an app update fails

#### Scenario: Timers keep apps current during the day
- **WHEN** the workstation remains running after boot
- **THEN** scheduled update services refresh the managed agent apps periodically
- **AND** those refreshes occur without waiting for the next manual app invocation

### Requirement: Mutable agent assets refresh automatically
The workstation SHALL refresh mutable agent assets on timers, including `skills.sh`-installed skills, plugins/extensions, OpenSpec refresh state, and Opencode OpenRouter programming-free-model config.

#### Scenario: Skills and extensions refresh from timers
- **WHEN** the scheduled mutable-asset updater runs
- **THEN** it refreshes installed skills and configured plugins/extensions using the workstation's persisted local state

#### Scenario: Opencode free-model config refreshes daily
- **WHEN** the scheduled Opencode model updater runs on a new day or stale boot
- **THEN** it regenerates the cached programming-free-model config for Opencode
- **AND** it preserves the last working generated config if the refresh fails

### Requirement: Update flows are atomic and preserve the last working local state
The workstation SHALL use failure-tolerant update flows so partial or failed app/asset refreshes do not leave the workstation without a working local toolchain.

#### Scenario: Failed app update leaves the prior version active
- **WHEN** an app install or app refresh fails mid-update
- **THEN** the previously active workstation version remains the one used by the stable invocation path

#### Scenario: Failed asset refresh leaves prior cached state available
- **WHEN** a mutable asset refresh fails
- **THEN** the workstation continues using the previously cached local asset state
