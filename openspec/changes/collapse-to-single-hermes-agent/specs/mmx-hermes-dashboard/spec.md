## MODIFIED Requirements

### Requirement: Dashboard environment view reports generic model endpoint configuration
The dashboard environment view SHALL report the effective Hermes runtime and configuration state in a provider-agnostic way instead of limiting the home view to a narrow runtime, provider, and profile summary. The home view SHALL expose grouped operator-facing facts for the configured runtime, managed agent model path, auxiliary overrides, and other detected Hermes feature areas without assuming OpenRouter-specific variables or a fixed profile topology.

#### Scenario: Home view shows grouped runtime and configuration facts
- **WHEN** an operator opens the dashboard home view
- **THEN** the runtime facts include grouped sections for the effective Hermes runtime and configuration state rather than only a flat summary
- **AND** the grouped sections include the configured managed-agent model path details
- **AND** the grouped sections include any detected auxiliary task overrides and other operator-facing Hermes feature areas that are configured at runtime
- **AND** the view remains usable for Hermes configs that point at providers other than OpenRouter

#### Scenario: Missing optional config groups do not break the home view
- **WHEN** a Hermes runtime does not configure some optional integrations or feature categories
- **THEN** the dashboard omits or de-emphasizes the absent groups without failing to render the home view
- **AND** the remaining runtime and configuration groups still render correctly

### Requirement: Dashboard enriches local-router configurations with live router state
When Hermes is configured to use the local router endpoint, the dashboard SHALL enrich the home view with live router alias and provider information from the router runtime surfaces as an additive section within the broader runtime/configuration view.

#### Scenario: Local router endpoint shows alias inventory and provider health
- **WHEN** the configured Hermes model endpoint is the local router and the router is healthy
- **THEN** the dashboard shows the logical aliases available from the router
- **AND** the dashboard shows candidate or inventory details associated with those aliases
- **AND** the dashboard shows current router provider health or readiness details
- **AND** the router-specific details appear without replacing the generic runtime and configuration sections

#### Scenario: Non-router endpoint falls back to config-derived environment facts
- **WHEN** the configured Hermes model endpoint is not the local router or the router enrichment request fails
- **THEN** the dashboard still renders the generic grouped runtime and configuration view
- **AND** the dashboard does not require router-specific data to show the home view

## REMOVED Requirements

### Requirement: Dashboard home view renders discovered profiles and sections generically
**Reason**: The dashboard no longer treats profile topology as the primary runtime abstraction in the supported image.
**Migration**: Render one managed-agent runtime surface and keep any legacy profile payload only as a compatibility shim during rollout.

## ADDED Requirements

### Requirement: Dashboard home view renders one managed agent runtime surface
The dashboard SHALL render the managed Hermes runtime as one operator-facing agent surface instead of a profile list.

#### Scenario: Home view centers on the managed agent
- **WHEN** an operator opens the dashboard home view after this change
- **THEN** the page identifies one managed Hermes agent as the supported runtime surface
- **AND** the home view does not require visible profile cards or default-profile labels to communicate the runtime state

#### Scenario: Legacy profile payloads do not redefine the UI model
- **WHEN** the backend serves a temporary compatibility payload for older clients
- **THEN** the primary dashboard UI still uses the single-agent terminology and layout
- **AND** the compatibility payload does not make profiles a first-class operator concept again
