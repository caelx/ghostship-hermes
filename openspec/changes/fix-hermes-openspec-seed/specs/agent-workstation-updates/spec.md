## MODIFIED Requirements

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
