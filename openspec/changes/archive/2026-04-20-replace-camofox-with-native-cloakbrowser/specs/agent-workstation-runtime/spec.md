## ADDED Requirements

### Requirement: Local browser automation uses image-native CloakBrowser through stock `agent-browser`
The workstation SHALL satisfy the supported Hermes local browser path by wiring stock `agent-browser` to an image-native CloakBrowser executable that appears as the effective local Chrome/Chromium runtime for Hermes browser automation.

#### Scenario: Hermes local browser path launches the native browser runtime
- **WHEN** a Hermes session uses the supported local browser path in the workstation image
- **THEN** the browser launch flows through stock `agent-browser`
- **AND** `agent-browser` starts the image-native CloakBrowser executable for the supported local browser session
- **AND** the supported persisted browser profile root is `/home/hermes/.local/state/cloakbrowser`

#### Scenario: Supported local browser path does not require operator-managed browser services
- **WHEN** an operator deploys the workstation image using the supported default browser contract
- **THEN** the local browser path does not require a repo-owned Camofox service, VNC sidecar, or CloakBrowser Manager service
- **AND** the supported local browser path does not depend on a downstream-provided browser-manager API URL or token

### Requirement: Supported browser runtime excludes retired browser shims
The workstation SHALL remove retired repo-owned browser runtime shims from the supported local browser contract once image-native CloakBrowser is adopted.

#### Scenario: Runtime no longer depends on Camofox-specific browser plumbing
- **WHEN** maintainers inspect the supported browser runtime in the image
- **THEN** the image does not require the Camofox HTTP shim, Camofox cache bootstrap, or Camofox-specific service supervision for the supported local browser path

#### Scenario: Runtime no longer advertises manager-wrapper browser control as supported
- **WHEN** maintainers inspect the supported browser runtime contract
- **THEN** the contract does not advertise `ghostship-cloakbrowser` as a supported workstation CLI
- **AND** the contract does not treat the CloakBrowser Manager API as part of the supported local-browser path
