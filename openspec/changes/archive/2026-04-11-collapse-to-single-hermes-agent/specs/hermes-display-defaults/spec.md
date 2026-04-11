## REMOVED Requirements

### Requirement: Managed Hermes profiles default to compact shared display settings
**Reason**: The runtime no longer scaffolds a fleet of managed profiles.
**Migration**: Apply the same compact shared display defaults to the single managed agent config.

### Requirement: Managed Hermes profiles stream CLI output by default
**Reason**: CLI display defaults now apply to one managed runtime surface instead of multiple profile configs.
**Migration**: Preserve streaming defaults on the single managed agent config.

## ADDED Requirements

### Requirement: The single managed Hermes agent defaults to compact shared display settings
The Hermes image SHALL scaffold the single managed agent with the repo's compact shared display policy so interactive CLI sessions default to a calmer operator-oriented presentation.

#### Scenario: Managed agent config is generated
- **WHEN** the image materializes or refreshes the managed single-agent config
- **THEN** the config sets `display.compact` to `true`
- **AND** the config sets `display.tool_progress` to `all`
- **AND** the config sets `display.background_process_notifications` to `result`
- **AND** the config sets `display.bell_on_complete` to `false`
- **AND** the config sets `display.show_reasoning` to `false`
- **AND** the config sets `display.skin` to `default`
- **AND** the managed runtime does not keep the previous verbose inspection-first defaults of `compact = false` and `tool_progress = verbose`

### Requirement: The single managed Hermes agent streams CLI output by default
The Hermes image SHALL scaffold the single managed agent with CLI display streaming enabled while preserving the compact shared display policy and the existing gateway streaming configuration.

#### Scenario: CLI display defaults are applied
- **WHEN** the managed single-agent config is generated for the image runtime
- **THEN** the config sets `display.streaming` to `true`
- **AND** the config keeps `display.compact` set to `true`
- **AND** the existing top-level `streaming.enabled` gateway behavior remains enabled independently of the CLI display setting
