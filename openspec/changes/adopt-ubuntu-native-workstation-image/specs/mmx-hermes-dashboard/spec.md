## MODIFIED Requirements

### Requirement: The dashboard SHALL serve the MMX browser entrypoint
The running dashboard SHALL serve the upstream Hermes native browser entrypoint on the supported dashboard port instead of the retired repo-packaged dashboard, while preserving a small Ghostship-owned `Console` extension backed by `ttyd`.

#### Scenario: Published browser port serves the upstream Hermes dashboard
- **WHEN** the Hermes container starts successfully and an operator opens the browser dashboard
- **THEN** the served entrypoint comes from the upstream Hermes native dashboard for the pinned Hermes release
- **AND** the browser surface does not depend on the retired repo-packaged dashboard backend or frontend

#### Scenario: Dashboard keeps a Ghostship-owned console entry
- **WHEN** an operator navigates the browser dashboard in the published image
- **THEN** the dashboard includes a `Console` tab or nav entry owned by the repo’s minimal patch layer
- **AND** that console path is the only required Ghostship-specific dashboard extension in the supported browser contract

### Requirement: Dashboard environment view reports generic model endpoint configuration
The dashboard environment and configuration surfaces SHALL expose the managed Hermes runtime through the upstream Hermes native views and APIs rather than through Ghostship-specific grouped cards or profile-era panels.

#### Scenario: Operator can inspect managed runtime facts through native Hermes views
- **WHEN** an operator opens the upstream Hermes dashboard against the managed single-agent image
- **THEN** the dashboard exposes the effective managed runtime and model configuration through native Hermes status/config views or their backing APIs
- **AND** the dashboard exposes env-backed provider and integration state through native Hermes env management views or their backing APIs
- **AND** the browser surface remains usable for the repo’s managed single-agent runtime without requiring named-profile topology or the retired custom dashboard sections

## REMOVED Requirements

### Requirement: Dashboard enriches local-router configurations with live router state
**Reason**: The new dashboard contract is upstream-owned except for the `Console` tab, so the repo is no longer committing to a broader Ghostship-specific router overlay inside the dashboard.
**Migration**: Operators SHALL inspect router-specific alias and provider state through router-native endpoints, service status, or CLI workflows instead of expecting browser-level router enrichment.

### Requirement: Dashboard home view uses modular feature cards
**Reason**: After this change the repo no longer owns the main dashboard layout implementation.
**Migration**: Validation and docs SHALL treat the upstream Hermes dashboard pages and APIs as the browser contract instead of asserting the retired MMX/HUDUI card layout.

### Requirement: Dashboard home view renders the managed agent and sections generically
**Reason**: The upstream Hermes dashboard organizes runtime data according to its own browser model rather than the repo’s custom managed-agent cards.
**Migration**: Operators SHALL validate the managed single-agent runtime through native Hermes views and APIs rather than through Ghostship-specific home cards.

## ADDED Requirements

### Requirement: Browser terminals remain available through the patched console tab
The supported browser contract SHALL keep browser terminal access available through the minimal patched `Console` tab backed by `ttyd`.

#### Scenario: Opening a console tab yields a reachable ttyd session
- **WHEN** an operator opens the `Console` tab from the patched dashboard
- **THEN** the runtime creates or reaches a `ttyd` session for that tab
- **AND** the browser terminal becomes reachable from the dashboard origin without the retired custom dashboard backend
