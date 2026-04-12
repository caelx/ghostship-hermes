## REMOVED Requirements

### Requirement: The dashboard SHALL serve the MMX browser entrypoint
**Reason**: The canonical browser surface is moving from the repo-specific MMX dashboard to `hermes-hudui`.
**Migration**: Replace MMX-specific browser assertions and UI expectations with the HUDUI frontend/backend contract plus the Ghostship `Console` tab.

### Requirement: Dashboard environment view reports generic model endpoint configuration
**Reason**: HUDUI does not use the current Ghostship-specific environment home view as its primary browser contract.
**Migration**: Move browser expectations to HUDUI's tabbed collector-driven surface and validate managed-runtime compatibility through HUDUI panels and APIs.

### Requirement: Dashboard home view uses modular feature cards
**Reason**: HUDUI defines its own top-level information architecture and panel layout.
**Migration**: Validate the HUDUI panel and tab structure instead of the previous Ghostship home-card composition.

### Requirement: Dashboard home view renders the managed agent and sections generically
**Reason**: HUDUI reintroduces a broader tab set, including profile- and agent-oriented panels, instead of centering the entire browser contract on one custom Ghostship home view.
**Migration**: Render the managed single-agent image layout through HUDUI-compatible panels rather than the old Ghostship-only home view.

## ADDED Requirements

### Requirement: The dashboard SHALL serve the Hermes HUDUI browser entrypoint
The running dashboard SHALL serve a browser entrypoint that aligns with `hermes-hudui` as the canonical browser product for the image, rather than the previous repo-specific MMX dashboard shell.

#### Scenario: Dashboard entrypoint loads the HUDUI surface
- **WHEN** the Hermes container starts successfully and an operator opens the browser dashboard
- **THEN** the browser service serves the packaged HUDUI frontend and backend contract
- **AND** the visible top-level navigation exposes the HUDUI-style dashboard tabs rather than the previous MMX-only shell
- **AND** the browser contract does not depend on the previous Ghostship-specific HTML markers or `/api/status` payload

### Requirement: HUDUI SHALL reflect the managed single-agent image layout
The HUDUI browser surface SHALL operate correctly against the image's managed single-agent layout rooted at `/home/hermes/.hermes`, without requiring a repo-owned named-profile fleet or the previous Ghostship-only browser data model.

#### Scenario: HUDUI renders the root managed agent state
- **WHEN** the managed Hermes runtime uses `/home/hermes/.hermes` as `HERMES_HOME`
- **THEN** HUDUI panels can read the managed runtime state from that root path
- **AND** the dashboard remains usable even when no repo-owned `profiles/` fleet exists under that managed runtime

#### Scenario: HUDUI uses its native API and live-update model
- **WHEN** the HUDUI frontend loads in the browser
- **THEN** it uses HUDUI-style `/api/*` endpoints and the `/ws` live-update channel as the browser contract
- **AND** the browser surface does not rely on the previous Ghostship-only dashboard API shape

### Requirement: Dashboard SHALL expose a Console tab backed by same-origin ttyd
The HUDUI dashboard SHALL include a Ghostship-specific `Console` tab that manages on-demand browser terminals through same-origin `ttyd` proxying.

#### Scenario: Opening the Console tab launches a terminal session
- **WHEN** an operator opens the `Console` tab and requests a browser terminal
- **THEN** the dashboard starts or attaches an on-demand `ttyd` session for that request
- **AND** the terminal is presented through the HUDUI browser surface without requiring a separate browser origin
- **AND** the operator can reach a shell rooted in the managed image terminal workspace contract

#### Scenario: Console remains usable while ttyd starts
- **WHEN** the operator opens a new console session and the backing `ttyd` process is still starting
- **THEN** the Console tab shows a visible connecting or loading state
- **AND** the live terminal attaches as soon as the backing session becomes ready without requiring the operator to reopen it

#### Scenario: Closing a console session tears down the backing terminal
- **WHEN** an operator closes a console session from the HUDUI surface
- **THEN** the dashboard tears down the corresponding on-demand `ttyd` session
- **AND** the console view removes that session from the visible browser state without leaving an orphaned terminal contract behind
