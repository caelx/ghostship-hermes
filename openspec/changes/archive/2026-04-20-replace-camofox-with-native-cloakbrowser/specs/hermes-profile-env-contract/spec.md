## ADDED Requirements

### Requirement: Default local browser runtime does not depend on operator-facing browser-service env
The workstation SHALL keep the supported default local browser path image-owned and SHALL NOT require downstream operators to supply Camofox or CloakBrowser Manager env to use the native local browser runtime.

#### Scenario: Supported local browser path works without browser-service env
- **WHEN** a downstream operator deploys the workstation image without `CAMOFOX_URL`, `CLOAKBROWSER_URL`, or `CLOAKBROWSER_TOKEN`
- **THEN** the supported default local browser path remains available
- **AND** the image does not require those env values for the supported stock `agent-browser` plus CloakBrowser workflow

#### Scenario: Manual CDP attachment remains a separate concern
- **WHEN** maintainers inspect the supported browser env inventory
- **THEN** the optional `BROWSER_CDP_URL` contract remains distinct from the supported default local browser path
- **AND** the supported default local browser path does not require operators to provide a CDP target

### Requirement: Browser plumbing env are documented as image-internal when retained
The workstation docs SHALL treat any retained browser-launch plumbing env for the supported default local browser path as image-internal rather than downstream-owned runtime knobs.

#### Scenario: Operator docs exclude retired browser-service env
- **WHEN** a downstream operator reads the documented runtime env inventory
- **THEN** the docs do not describe `CAMOFOX_URL`, `CLOAKBROWSER_URL`, or `CLOAKBROWSER_TOKEN` as supported downstream env for the workstation browser contract

#### Scenario: Internal browser-launch env are not exposed as supported knobs
- **WHEN** maintainers document the supported default local browser path
- **THEN** any image-owned browser-launch settings used to point `agent-browser` at CloakBrowser are described as internal image plumbing
- **AND** the docs do not tell downstream operators to override those internal settings for the supported path
