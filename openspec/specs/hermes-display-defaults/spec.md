## ADDED Requirements

### Requirement: Managed Hermes profiles default to verbose tool progress
The Hermes image SHALL scaffold each managed profile with verbose tool progress enabled so interactive CLI sessions expose full tool progress details by default.

#### Scenario: Managed profile config is generated
- **WHEN** the image materializes or refreshes the managed `assistant`, `operations`, and `supervisor` profiles
- **THEN** each managed profile config sets `display.tool_progress` to `verbose`
- **AND** the managed runtime does not fall back to the previous terse default of `new`

### Requirement: Managed Hermes profiles keep full tool previews visible
The Hermes image SHALL scaffold each managed profile with unrestricted tool preview length so operators can inspect full command and path previews during interactive sessions.

#### Scenario: Tool preview defaults are applied
- **WHEN** a managed profile config is generated for the image runtime
- **THEN** the config sets `display.tool_preview_length` to `0`
- **AND** Hermes treats the preview length as unlimited rather than truncating commands or file paths by default

### Requirement: Managed Hermes profiles stream CLI output by default
The Hermes image SHALL scaffold each managed profile with CLI display streaming enabled while preserving the existing gateway streaming configuration.

#### Scenario: CLI display defaults are applied
- **WHEN** a managed profile config is generated for the image runtime
- **THEN** the config sets `display.streaming` to `true`
- **AND** the config keeps `display.compact` set to `false`
- **AND** the existing top-level `streaming.enabled` gateway behavior remains enabled independently of the CLI display setting
