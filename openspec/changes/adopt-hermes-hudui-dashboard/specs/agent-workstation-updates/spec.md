## ADDED Requirements

### Requirement: Runtime validation proves the HUDUI browser contract
The workstation SHALL validate the HUDUI browser surface as the published dashboard contract instead of continuing to validate the previous Ghostship-only dashboard markers and APIs.

#### Scenario: Smoke test validates the HUDUI dashboard surface
- **WHEN** maintainers run the Hermes image dashboard smoke test
- **THEN** the test verifies the managed browser service is active
- **AND** the test verifies the browser root and HUDUI backend endpoints are reachable on the published browser port
- **AND** the test verifies the browser contract no longer depends on the previous Ghostship `/api/status` or MMX-only entrypoint markers

#### Scenario: Browser-driven validation opens the Console tab
- **WHEN** maintainers run browser-driven dashboard validation
- **THEN** the validation opens the HUDUI browser surface
- **AND** the validation exercises the `Console` tab through the real browser UI
- **AND** the validation proves that a browser terminal becomes visible and usable from that HUDUI console workflow

### Requirement: Persistence validation preserves the HUDUI dashboard contract
The workstation SHALL prove that the HUDUI dashboard surface and its configured browser integrations remain valid after container replacement with persisted runtime state.

#### Scenario: Replacement keeps the HUDUI browser service healthy
- **WHEN** maintainers run the persistence validation through container replacement
- **THEN** the validation verifies the managed browser service comes back healthy after replacement
- **AND** the validation verifies the HUDUI browser surface remains reachable on the published port

#### Scenario: Replacement keeps the Console workflow available
- **WHEN** the container is replaced while `/home/hermes` and `/workspace` persist
- **THEN** the validation verifies the HUDUI console workflow can still open a browser terminal after replacement
- **AND** the validation does not rely on the removed Ghostship dashboard API contract to prove that behavior

### Requirement: Remote dashboard validation exposes a browseable tunnel
The workstation SHALL make the live HUDUI surface on a remote validation host browseable from the maintainer's local machine during remote dashboard verification.

#### Scenario: Remote validation on chill-penguin-root2 creates a local browser path
- **WHEN** maintainers validate the HUDUI dashboard on `chill-penguin-root2`
- **THEN** the validation creates a tunnel from the remote dashboard port to a local port on the maintainer machine
- **AND** the resulting local URL can be opened in a browser to inspect the live remote HUDUI surface interactively
- **AND** the remote validation flow does not require direct host-level exposure of the dashboard port to the public network
