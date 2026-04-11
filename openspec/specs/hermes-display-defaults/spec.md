## MODIFIED Requirements

### Requirement: Managed Hermes runtime defaults to compact shared display settings
The Hermes image SHALL scaffold the managed runtime with the repo's compact shared display policy so interactive CLI sessions default to a calmer operator-oriented presentation.

#### Scenario: Managed config is generated
- **WHEN** the image materializes or refreshes the managed Hermes config
- **THEN** the managed config sets `display.compact` to `true`
- **AND** the managed config sets `display.tool_progress` to `all`
- **AND** the managed config sets `display.background_process_notifications` to `result`
- **AND** the managed config sets `display.bell_on_complete` to `false`
- **AND** the managed config sets `display.show_reasoning` to `false`
- **AND** the managed config sets `display.skin` to `default`
- **AND** the managed runtime does not keep the previous verbose inspection-first defaults of `compact = false` and `tool_progress = verbose`

### Requirement: Managed Hermes runtime streams CLI output by default
The Hermes image SHALL scaffold the managed runtime with CLI display streaming enabled while preserving the compact shared display policy and the existing gateway streaming configuration.

#### Scenario: CLI display defaults are applied
- **WHEN** the managed Hermes config is generated for the image runtime
- **THEN** the config sets `display.streaming` to `true`
- **AND** the config keeps `display.compact` set to `true`
- **AND** the existing top-level `streaming.enabled` gateway behavior remains enabled independently of the CLI display setting
