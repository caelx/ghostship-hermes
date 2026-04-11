## MODIFIED Requirements

### Requirement: The managed gateway publishes a live `gateway.pid`
The repo-managed gateway service SHALL maintain a `gateway.pid` marker at the root managed Hermes home that matches the live managed gateway process used for Hermes health checks and status reporting.

#### Scenario: Managed gateway start writes the current PID
- **WHEN** the managed gateway service starts
- **THEN** `/home/hermes/.hermes/gateway.pid` is created or replaced before the long-running gateway process begins serving the managed runtime
- **AND** the file contains the PID of the active managed gateway process rather than a stale earlier run

#### Scenario: Managed gateway replacement refreshes stale pidfiles
- **WHEN** the managed gateway service restarts or replaces an earlier process
- **THEN** any stale `gateway.pid` content from the earlier run is removed or overwritten
- **AND** the resulting `gateway.pid` points to the current managed gateway process rather than the previous run

### Requirement: Managed gateway liveness markers follow the service lifecycle
Repo-owned managed gateway marker files SHALL stay aligned with the managed service lifecycle so dashboard and Hermes health/status surfaces do not report false negatives for the live repo-managed gateway.

#### Scenario: Live managed gateway is visible to dashboard and Hermes health checks
- **WHEN** the repo-managed gateway process is running under the managed systemd service
- **THEN** `/home/hermes/.hermes/gateway.pid` exists while that service remains active
- **AND** dashboard status and Hermes health checks can observe the managed gateway as running from that marker

#### Scenario: Stopped managed gateway does not leave misleading liveness state
- **WHEN** the managed gateway service stops cleanly or is replaced during restart
- **THEN** stale repo-owned liveness markers are removed or invalidated during the stop lifecycle
- **AND** later health checks do not report a stopped managed gateway as still live because of stale marker state
