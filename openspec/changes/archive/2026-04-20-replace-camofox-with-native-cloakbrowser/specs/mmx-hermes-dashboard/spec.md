## MODIFIED Requirements

### Requirement: The dashboard SHALL serve the MMX browser entrypoint
The running dashboard SHALL serve the upstream Hermes native browser entrypoint on the supported published web port instead of the retired repo-packaged dashboard, while preserving a small Ghostship-owned `Terminal` entry backed by a separate `ttyd` sidecar as the only required repo-owned dashboard extension.

#### Scenario: Published browser port serves the upstream Hermes dashboard
- **WHEN** the Hermes container starts successfully and an operator opens the browser dashboard
- **THEN** the served entrypoint comes from the upstream Hermes native dashboard for the pinned Hermes release
- **AND** the browser surface does not depend on the retired repo-packaged dashboard backend or frontend

#### Scenario: Dashboard keeps a Ghostship-owned terminal entry
- **WHEN** an operator navigates the browser dashboard in the published image
- **THEN** the dashboard includes a `Terminal` entry owned by the repo’s minimal patch layer
- **AND** that terminal entry is the only required Ghostship-specific dashboard extension in the supported browser contract
- **AND** the supported dashboard contract does not require a repo-owned Browser live-view entry or iframe
