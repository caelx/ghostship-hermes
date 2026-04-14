## MODIFIED Requirements

### Requirement: The dashboard SHALL serve the MMX browser entrypoint
The running dashboard SHALL serve the upstream Hermes native browser entrypoint from the pinned Hermes runtime on the upstream dashboard port `9119` instead of serving a repo-packaged MMX/HUDUI dashboard on the repo’s former `7681` contract.

#### Scenario: Published browser port serves the upstream Hermes dashboard
- **WHEN** the Hermes container starts successfully and an operator opens the browser dashboard on port `9119`
- **THEN** the served entrypoint comes from the upstream Hermes native dashboard for the pinned Hermes release
- **AND** the browser surface does not depend on the repo-packaged `packages/hermes-dashboard` frontend or FastAPI controller
- **AND** the browser contract no longer requires the MMX terminal-launch action or any Ghostship-specific dashboard chrome

#### Scenario: Native dashboard remains usable when embedded cross-origin
- **WHEN** an operator embeds the published dashboard origin in an iframe from a different origin
- **THEN** the browser response does not deny that embed through runtime frame headers or equivalent policy
- **AND** the upstream Hermes dashboard loads successfully inside the iframe
- **AND** the core native dashboard interactions used for status/config/env/session inspection still function inside the embedded view

### Requirement: Dashboard environment view reports generic model endpoint configuration
The dashboard environment and configuration surfaces SHALL expose the managed Hermes runtime through the upstream Hermes native status, config, and env views/APIs instead of through Ghostship-specific grouped cards or profile-era panels.

#### Scenario: Operator can inspect managed runtime facts through native Hermes views
- **WHEN** an operator opens the upstream Hermes dashboard against the managed single-agent image
- **THEN** the dashboard exposes the effective managed runtime and model configuration through native Hermes status/config views or their backing APIs
- **AND** the dashboard exposes env-backed provider and integration state through native Hermes env management views or their backing APIs
- **AND** the dashboard remains usable for the repo’s managed single-agent runtime without requiring named-profile topology or Ghostship-specific browser sections

#### Scenario: Managed config edits target the same runtime files Hermes uses
- **WHEN** an operator edits managed configuration or env values through the upstream Hermes dashboard
- **THEN** those edits target the same managed runtime config and env files that the Hermes CLI and managed services read
- **AND** the browser surface does not depend on a separate Ghostship-only config projection layer

## REMOVED Requirements

### Requirement: Dashboard enriches local-router configurations with live router state
**Reason**: The upstream Hermes native dashboard does not own the repo’s custom local-router enrichment contract, and this change replaces the custom dashboard completely rather than recreating that browser-specific overlay.
**Migration**: Operators and validation flows SHALL inspect router-specific alias and provider state through router-native endpoints, service status, or CLI workflows instead of expecting Ghostship dashboard enrichment.

### Requirement: Dashboard home view uses modular feature cards
**Reason**: After replacement, the repo no longer owns the dashboard layout implementation, card system, or MMX/HUDUI visual contract.
**Migration**: Validation and docs SHALL treat upstream Hermes pages and APIs as the browser contract instead of asserting a Ghostship-specific card layout.

### Requirement: Dashboard home view renders the managed agent and sections generically
**Reason**: The upstream Hermes dashboard organizes runtime data according to its own native browser model rather than the repo’s custom managed-agent fact cards.
**Migration**: Operators SHALL validate the managed single-agent runtime through native Hermes pages and APIs rather than through Ghostship-specific home cards.

### Requirement: Browser terminals feel responsive during startup and teardown
**Reason**: The `Console` tab and same-origin `ttyd` browser contract are removed as part of fully replacing the custom dashboard.
**Migration**: Browser terminal launch SHALL not be treated as a supported dashboard capability; admin and debug shell workflows SHALL use normal CLI/container access instead.
