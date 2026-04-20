## ADDED Requirements

### Requirement: Publication validation proves the native local browser contract
The publication workflow SHALL validate the supported native local browser path on the final workstation image artifact instead of relying on retired Camofox or manager-wrapper browser surfaces.

#### Scenario: Final image validation proves native browser launch
- **WHEN** the repository prepares to publish a workstation image with the supported native browser path
- **THEN** the workflow validates that stock `agent-browser` can execute a non-destructive browser action using the supported image-native CloakBrowser runtime on the final image artifact
- **AND** the workflow does not treat Camofox-only health checks or manager-wrapper API checks as proof of browser readiness

#### Scenario: Final image validation proves persisted browser profile behavior
- **WHEN** the repository prepares to publish a workstation image with the supported native browser path
- **THEN** the workflow validates the supported browser profile behavior across restart or full container recreation on the final image artifact
- **AND** the workflow does not publish the image if the supported browser profile contract fails after persistence reuse

### Requirement: Manual live-host validation on `chill-penguin` remains mandatory
The repository SHALL require manual validation of the supported native local browser contract on `chill-penguin` before the browser-contract replacement is treated as deployment-proof.

#### Scenario: Maintainer manually validates the deployed browser contract on `chill-penguin`
- **WHEN** maintainers test a candidate image or deployment for the supported native browser path
- **THEN** they manually run the browser-validation flow on `chill-penguin`
- **AND** that manual validation proves stock `agent-browser` can launch the image-native CloakBrowser runtime on the live host
- **AND** that manual validation proves `/home/hermes/.local/state/cloakbrowser` persists across restart or full container recreation on the live host
- **AND** maintainers do not treat CI-only or local-only validation as sufficient deployment proof for this change

### Requirement: Publication docs remove retired browser surfaces
The repository SHALL keep published deployment guidance aligned with the native CloakBrowser-backed workstation contract.

#### Scenario: Operator reads browser deployment guidance
- **WHEN** a downstream operator reads the published image guidance for browser behavior
- **THEN** the docs describe the supported native local browser path backed by stock `agent-browser` plus image-native CloakBrowser
- **AND** the docs do not describe Camofox services, `/camofox/` browser paths, or `ghostship-cloakbrowser` as supported workstation surfaces
