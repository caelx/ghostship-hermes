## ADDED Requirements

### Requirement: Agent apps update automatically in persisted state
The workstation SHALL install and update `codex`, `gemini-cli`, `opencode`, `openspec`, and `skills` automatically on boot and on timers using persisted install roots under the workstation state.

#### Scenario: Boot update converges the persisted app installs
- **WHEN** the workstation boots
- **THEN** the boot updater checks and refreshes the managed agent apps using the persisted workstation layout
- **AND** the last working local version remains active if an update fails

#### Scenario: Timers refresh apps during the day
- **WHEN** the workstation remains running after boot
- **THEN** scheduled updater services refresh the managed agent apps without waiting for the next manual invocation

### Requirement: Mutable agent assets refresh automatically in persisted state
The workstation SHALL refresh mutable agent assets on boot and on timers using persisted state, including `skills.sh`-installed skills, plugins/extensions, OpenSpec refresh state, and Opencode programming free-model config.

#### Scenario: Mutable assets refresh through persisted state
- **WHEN** the scheduled asset updater runs
- **THEN** it refreshes the configured mutable agent assets in persisted storage
- **AND** those refreshed assets remain available after container restart or replacement

#### Scenario: OpenSpec refresh reapplies the current Ghostship override text
- **WHEN** the workstation refreshes OpenSpec instruction roots in a repo under persisted state
- **THEN** it reapplies the current Ghostship override blocks after `openspec update`
- **AND** the regenerated propose override instructs agents to create or reuse `.worktrees/<name>/`

#### Scenario: Opencode free-model config refreshes daily
- **WHEN** the scheduled Opencode model updater runs on a new day or stale boot
- **THEN** it regenerates the cached Opencode programming free-model config in persisted state

### Requirement: Failed updates preserve the last working local state
The workstation SHALL use failure-tolerant update flows so partial or failed app/asset refreshes do not leave the workstation without a working local toolchain or cached local state.

#### Scenario: Failed app update leaves prior version active
- **WHEN** an app update fails mid-refresh
- **THEN** the previously active local app version remains the one used by the stable invocation path

#### Scenario: Failed asset refresh leaves prior cached state available
- **WHEN** a mutable asset refresh fails
- **THEN** the workstation continues using the previously cached local asset state
