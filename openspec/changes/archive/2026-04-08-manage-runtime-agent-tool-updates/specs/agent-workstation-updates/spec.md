## MODIFIED Requirements

### Requirement: Agent apps update automatically in persisted state
The workstation SHALL install and update the in-scope agent CLIs automatically on boot and on timers using persisted install roots under the workstation state.

#### Scenario: Boot update converges the persisted app installs
- **WHEN** the workstation boots
- **THEN** the boot updater checks and refreshes the managed agent apps using the persisted workstation layout
- **AND** the in-scope npm CLI set includes `@openai/codex`, `@google/gemini-cli`, `opencode-ai`, and `agent-browser`
- **AND** the last working local version remains active if an update fails

#### Scenario: Timers refresh apps during the day
- **WHEN** the workstation remains running after boot
- **THEN** scheduled updater services refresh the managed agent apps without waiting for the next manual invocation

## ADDED Requirements

### Requirement: Hermes and stable operator tools update through the user Nix profile
The workstation SHALL keep Hermes itself and the stable operator-facing CLI set updateable through the `hermes` user Nix profile.

#### Scenario: Boot and timer updates include Hermes and stable user tools
- **WHEN** the managed updater runs at boot or on its daily timer
- **THEN** it checks or upgrades the user-installed Nix profile packages that provide `hermes`, `git`, `curl`, `jq`, `python3`, `nix`, `ripgrep`, and `node`/`npm`
- **AND** any failure leaves the previously working user-installed versions active

### Requirement: Supported doctor warnings are reduced through the managed runtime layers
The workstation SHALL wire the runtime dependencies and shared env needed for the Hermes doctor checks that correspond to intentionally supported features.

#### Scenario: Doctor reflects supported features
- **WHEN** the operator runs `hermes -p <profile> doctor`
- **THEN** the managed runtime reduces avoidable warnings for the supported Hermes, Codex, browser, GitHub-token, and Home Assistant paths
- **AND** intentionally unsupported optional integrations may still report warnings
