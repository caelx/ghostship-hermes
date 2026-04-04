## REMOVED Requirements

### Requirement: Agent apps update automatically in persisted state
**Reason**: The rebuilt image removes Ghostship-managed Codex, Gemini CLI, Opencode, OpenSpec, and `skills` app installation/update behavior from the default runtime.

**Migration**: Runtime docs, tests, and service wiring SHALL stop describing boot-time or timer-driven Ghostship app updates as part of the image contract.

### Requirement: Mutable agent assets refresh automatically in persisted state
**Reason**: The rebuilt image removes Ghostship-managed mutable asset refresh flows and their persisted runtime state.

**Migration**: Runtime docs and tests SHALL stop expecting `skills.sh`, extension/plugin refresh, OpenSpec override reapplication, or Opencode model refresh behavior from the image runtime.

### Requirement: Failed updates preserve the last working local state
**Reason**: The corresponding Ghostship-managed update subsystem is being removed from the rebuilt runtime.

**Migration**: Validation for the rebuilt image SHALL focus on the retained runtime package set and persisted user-level state rather than Ghostship-managed app refresh rollback behavior.
