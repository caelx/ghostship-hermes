## MODIFIED Requirements

### Requirement: The dashboard SHALL serve the Hermes browser entrypoint
The running dashboard SHALL serve a browser entrypoint that preserves the Hermes identity while presenting a modern glass-style visual treatment instead of the older MMX-specific aesthetic.

#### Scenario: Dashboard entrypoint exposes the Hermes Glass treatment
- **WHEN** the Hermes container starts successfully and an operator opens the browser dashboard
- **THEN** the dashboard serves a static HTML entrypoint from the packaged dashboard
- **AND** that entrypoint presents the modern Hermes Glass visual treatment rather than the earlier MMX-specific styling
- **AND** the interface still preserves the same terminal-launch and session-management behavior
