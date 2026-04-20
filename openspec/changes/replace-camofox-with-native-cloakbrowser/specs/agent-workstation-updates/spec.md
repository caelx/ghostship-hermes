## ADDED Requirements

### Requirement: Runtime validation proves the native persistent-browser path
The workstation SHALL validate the supported local browser contract with a non-destructive browser smoke that proves stock `agent-browser` can launch the image-native CloakBrowser runtime with the supported persisted profile path.

#### Scenario: Validation exercises native browser launch
- **WHEN** maintainers run the Hermes image validation suite for a build that advertises the native local browser path
- **THEN** the suite executes a non-destructive browser action through stock `agent-browser`
- **AND** that action uses the supported image-native CloakBrowser runtime rather than only proving command discovery

#### Scenario: Validation proves browser profile persistence
- **WHEN** maintainers run restart or container-replacement validation for the workstation image
- **THEN** the suite verifies that the supported browser profile state remains available from the persisted `/home/hermes` tree after the runtime comes back
- **AND** the suite does not treat a fresh empty browser profile after restart as a passing result

### Requirement: Validation excludes retired browser surfaces
The workstation SHALL stop treating retired browser shims as proof of the supported browser contract.

#### Scenario: Validation does not require Camofox-only health endpoints
- **WHEN** maintainers run image or live validation for the supported browser path
- **THEN** the validation does not require Camofox-specific health endpoints, cache markers, or helper modules to pass

#### Scenario: Validation does not require manager-wrapper browser APIs
- **WHEN** maintainers run image or live validation for the supported browser path
- **THEN** the validation does not require `ghostship-cloakbrowser` commands or CloakBrowser Manager API calls to pass
