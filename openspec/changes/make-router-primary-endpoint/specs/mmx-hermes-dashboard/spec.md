## ADDED Requirements

### Requirement: Dashboard environment view reports generic model endpoint configuration
The dashboard environment view SHALL report the configured root and per-profile Hermes model endpoint details in a provider-agnostic way instead of assuming OpenRouter-specific environment variables are the primary source of truth.

#### Scenario: Environment view shows root and profile endpoint settings
- **WHEN** an operator opens the dashboard home view
- **THEN** the runtime facts include the root Hermes model endpoint and root default model
- **AND** each managed profile entry includes its configured model endpoint and default model
- **AND** the view remains usable for Hermes configs that point at providers other than OpenRouter

### Requirement: Dashboard enriches local-router configurations with live router state
When Hermes is configured to use the local router endpoint, the dashboard SHALL enrich the environment view with live router alias and provider information from the router runtime surfaces.

#### Scenario: Local router endpoint shows alias inventory and provider health
- **WHEN** the configured Hermes model endpoint is the local router and the router is healthy
- **THEN** the dashboard shows the logical aliases available from the router
- **AND** the dashboard shows candidate or inventory details associated with those aliases
- **AND** the dashboard shows current router provider health or readiness details

#### Scenario: Non-router endpoint falls back to config-derived environment facts
- **WHEN** the configured Hermes model endpoint is not the local router or the router enrichment request fails
- **THEN** the dashboard still renders the generic root and profile endpoint configuration
- **AND** the dashboard does not require router-specific data to show the home view
