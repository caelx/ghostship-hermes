## ADDED Requirements

### Requirement: The image SHALL provide a minimal browser dashboard
The image SHALL provide a small browser-facing dashboard that is limited to the minimum Ghostship-specific behavior still required after the upstream-aligned rebuild.

#### Scenario: Dashboard serves a simple operator entrypoint
- **WHEN** the rebuilt container starts successfully
- **THEN** the browser-facing dashboard serves a static HTML entrypoint
- **AND** that entrypoint exposes a clear action for opening a terminal into the running Hermes environment
- **AND** the entrypoint keeps the old Hermes logo while using a darker modern visual treatment without serif typography

### Requirement: Browser terminals SHALL be launched on demand and remain non-persistent
Browser terminal sessions SHALL be created only when requested, SHALL support explicit dashboard-driven teardown, and SHALL NOT be managed as long-lived background services.

#### Scenario: Opening a terminal creates an ephemeral session
- **WHEN** an operator requests a browser terminal from the dashboard
- **THEN** the runtime launches or proxies a `ttyd` session for that request
- **AND** the new terminal is represented as a focused tab in the dashboard
- **AND** the focused tab appears immediately even if the `ttyd` process is still starting
- **AND** the session starts in `/home/hermes`
- **AND** the tab label reflects the shell cwd while idle and the foreground command name while work is running
- **AND** each tab uses a single-line label rather than a multi-line summary
- **AND** switching back to an already-open tab reuses the live session instead of dropping into a reconnect prompt
- **AND** the session is not represented as a persistent systemd service that remains running after the browser session ends

#### Scenario: Closing a terminal tears down the ephemeral session
- **WHEN** an operator closes a browser terminal from the dashboard
- **THEN** the runtime tears down the corresponding on-demand `ttyd` session
- **AND** the closed session's tab is removed from the dashboard
- **AND** the dashboard returns to a blank home state when no terminals remain
- **AND** no background terminal service remains running for that closed session

### Requirement: Dashboard runtime SHALL NOT depend on profile reconciliation services
The dashboard implementation SHALL NOT require the current Ghostship profile reconciler or per-profile background terminal management.

#### Scenario: Dashboard comes up without profile orchestrators
- **WHEN** maintainers inspect the rebuilt browser/runtime service graph
- **THEN** the dashboard stack does not depend on a profile reconciler loop
- **AND** it does not require pre-generated per-profile `ttyd` services to be running before the dashboard can be used
