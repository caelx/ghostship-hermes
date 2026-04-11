## MODIFIED Requirements

### Requirement: The dashboard SHALL serve the MMX browser entrypoint
The running dashboard SHALL serve a browser entrypoint that preserves the Hermes identity while presenting a more distinctive futuristic MMX-style visual treatment with purposeful animation instead of a plain utilitarian panel layout.

#### Scenario: Dashboard entrypoint exposes a stronger Hermes visual identity
- **WHEN** the Hermes container starts successfully and an operator opens the browser dashboard
- **THEN** the dashboard serves a static HTML entrypoint from the packaged dashboard
- **AND** that entrypoint presents a futuristic Hermes-aligned visual treatment rather than a generic minimal card layout
- **AND** the interface uses intentional animations or transitions to reinforce state changes and section reveals without obscuring core runtime facts
- **AND** the entrypoint still exposes the MMX terminal-launch action rather than the older dashboard copy contract

### Requirement: Dashboard environment view reports generic model endpoint configuration
The dashboard environment view SHALL report the effective managed Hermes runtime and configuration state in a provider-agnostic way instead of limiting the home view to a narrow runtime, provider, or profile summary. The home view SHALL expose grouped operator-facing facts for the configured runtime, the managed agent, the model path, auxiliary overrides, and other detected Hermes feature areas without assuming OpenRouter-specific variables or any named-profile topology.

#### Scenario: Home view shows grouped runtime and configuration facts
- **WHEN** an operator opens the dashboard home view
- **THEN** the runtime facts include grouped sections for the effective Hermes runtime and configuration state rather than only a flat summary
- **AND** the grouped sections include the managed agent path, service, and model endpoint details
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

## MODIFIED Requirements

### Requirement: Dashboard home view uses modular feature cards
The dashboard home view SHALL render smaller feature-oriented cards instead of relying on a few large fixed panels, and those cards SHALL stack and reflow automatically as sections appear, disappear, or change size.

#### Scenario: Smaller cards reflow across viewport sizes
- **WHEN** an operator opens the dashboard on a narrow or wide viewport
- **THEN** the home view arranges its feature cards in a responsive layout that stacks and wraps naturally
- **AND** no single fixed panel is required to span the entire page just to render managed-agent or configuration information

#### Scenario: Optional sections fit into the card layout without layout breakage
- **WHEN** the runtime exposes additional feature groups such as browser, memory, security, messaging, or env-backed capability status
- **THEN** the dashboard renders those groups as additional feature cards within the same responsive card system
- **AND** the layout remains readable without requiring a dashboard-specific redesign for each new group

### Requirement: Dashboard home view renders the managed agent and sections generically
The dashboard SHALL render the managed agent and feature sections from runtime data instead of hardcoding profile names, fixed profile counts, or a profile-list-specific layout.

#### Scenario: Managed agent facts render without profile topology
- **WHEN** the Hermes runtime reports one managed agent and no profile list
- **THEN** the dashboard renders the managed agent in the home view using the same generic fact-card system as the other runtime sections
- **AND** the page does not depend on hardcoded profile names or any profile topology

#### Scenario: Unknown future section fields degrade gracefully
- **WHEN** the backend adds new facts within an existing feature group or introduces a new optional section
- **THEN** the dashboard renders the known high-signal fields while tolerating additional data without throwing rendering errors
- **AND** operators can still inspect the existing runtime and configuration cards successfully

### Requirement: Browser terminals feel responsive during startup and teardown
Browser terminal tabs SHALL react immediately in the dashboard UI even when the underlying `ttyd` process is still starting or shutting down in the background.

#### Scenario: Opening a terminal shows the tab before ttyd is ready
- **WHEN** an operator requests a browser terminal from the dashboard
- **THEN** the dashboard creates and focuses the new terminal tab immediately
- **AND** the terminal view shows a connecting or loading state until `ttyd` becomes available
- **AND** the live terminal attaches as soon as the backing `ttyd` session is ready without requiring the operator to reopen the tab

#### Scenario: Closing a terminal removes it from the UI before teardown completes
- **WHEN** an operator closes a browser terminal from the dashboard
- **THEN** the dashboard removes the tab from the visible UI immediately
- **AND** the runtime may continue shutting down the backing `ttyd` session asynchronously in the background
- **AND** the operator does not need to wait for backend teardown completion for the tab to disappear from the page
