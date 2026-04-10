## MODIFIED Requirements

### Requirement: Managed Hermes profiles default to compact shared display settings
The Hermes image SHALL scaffold each managed profile with the repo's compact shared display policy so interactive CLI sessions default to a calmer operator-oriented presentation.

#### Scenario: Managed profile config is generated
- **WHEN** the image materializes or refreshes the managed `assistant`, `operations`, and `supervisor` profiles
- **THEN** each managed profile config sets `display.compact` to `true`
- **AND** each managed profile config sets `display.tool_progress` to `all`
- **AND** each managed profile config sets `display.background_process_notifications` to `result`
- **AND** each managed profile config sets `display.bell_on_complete` to `false`
- **AND** each managed profile config sets `display.show_reasoning` to `false`
- **AND** each managed profile config sets `display.skin` to `default`
- **AND** the managed runtime does not keep the previous verbose inspection-first defaults of `compact = false` and `tool_progress = verbose`

### Requirement: Managed Hermes profiles stream CLI output by default
The Hermes image SHALL scaffold each managed profile with CLI display streaming enabled while preserving the compact shared display policy and the existing gateway streaming configuration.

#### Scenario: CLI display defaults are applied
- **WHEN** a managed profile config is generated for the image runtime
- **THEN** the config sets `display.streaming` to `true`
- **AND** the config keeps `display.compact` set to `true`
- **AND** the existing top-level `streaming.enabled` gateway behavior remains enabled independently of the CLI display setting

## REMOVED Requirements

### Requirement: Managed Hermes profiles keep full tool previews visible
**Reason**: The new managed display policy no longer includes an explicit unlimited preview-length override as part of the shared default contract.
**Migration**: Operators who still want unrestricted tool previews should set `display.tool_preview_length = 0` in their own Hermes profile config.
