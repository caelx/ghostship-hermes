## ADDED Requirements

### Requirement: The Hermes image SHALL install the packaged MMX dashboard
The Hermes image SHALL install the `packages/hermes-dashboard` package as the canonical browser-facing dashboard implementation, and that package SHALL include the runnable dashboard entrypoint together with the bundled static frontend assets it serves.

#### Scenario: Packaged dashboard artifact is usable in the image path
- **WHEN** maintainers build or inspect the packaged dashboard artifact consumed by the Hermes image
- **THEN** the artifact provides the `hermes-dashboard` program entrypoint
- **AND** the packaged artifact includes the MMX dashboard static assets required to serve the browser UI without a repo-local asset directory

### Requirement: The dashboard SHALL serve the MMX browser entrypoint
The running dashboard SHALL serve the MMX-style browser entrypoint from the packaged dashboard assets instead of the older dashboard copy or markup contract.

#### Scenario: Dashboard entrypoint exposes MMX UI markers
- **WHEN** the Hermes container starts successfully and an operator opens the browser dashboard
- **THEN** the dashboard serves a static HTML entrypoint from the packaged dashboard
- **AND** that entrypoint keeps the old Hermes logo while using the MMX visual treatment
- **AND** that entrypoint exposes the MMX terminal-launch action rather than the older dashboard copy contract

### Requirement: Browser terminals SHALL be launched on demand and remain non-persistent
Browser terminal sessions SHALL be created only when requested, SHALL support explicit dashboard-driven teardown, and SHALL NOT be managed as long-lived background services.

#### Scenario: Opening a terminal creates an ephemeral session
- **WHEN** an operator requests a browser terminal from the dashboard
- **THEN** the runtime launches or proxies a `ttyd` session for that request
- **AND** the new terminal is represented as a focused tab in the dashboard
- **AND** the focused tab appears immediately even if the `ttyd` process is still starting
- **AND** the session starts in `/home/hermes`
- **AND** the tab label reflects the shell cwd while idle and the foreground command name while work is running
- **AND** switching back to an already-open tab reuses the live session instead of dropping into a reconnect prompt
- **AND** the session is not represented as a persistent systemd service that remains running after the browser session ends

#### Scenario: Closing a terminal tears down the ephemeral session
- **WHEN** an operator closes a browser terminal from the dashboard
- **THEN** the runtime tears down the corresponding on-demand `ttyd` session
- **AND** the closed session's tab is removed from the dashboard
- **AND** the dashboard returns to a blank home state when no terminals remain
- **AND** no background terminal service remains running for that closed session

### Requirement: Dashboard terminal proxying SHALL remain same-origin
The dashboard SHALL continue to proxy terminal HTTP and websocket traffic from its own origin to loopback-only `ttyd` listeners so terminal sessions remain attached when operators switch tabs.

#### Scenario: Terminal websocket uses the dashboard origin
- **WHEN** an operator loads or reconnects to an already-open dashboard terminal tab
- **THEN** the browser terminal connects through the dashboard origin rather than directly to a separate public `ttyd` port
- **AND** the live session stays attached instead of falling into a reconnect overlay caused by origin mismatch

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
