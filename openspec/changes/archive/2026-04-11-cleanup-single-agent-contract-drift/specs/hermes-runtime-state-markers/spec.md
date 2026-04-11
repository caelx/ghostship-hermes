## REMOVED Requirements

### Requirement: Managed profile gateways publish a live `gateway.pid`
**Reason**: The supported image topology no longer maintains per-profile liveness markers for a fleet of named-profile gateways.
**Migration**: Publish one managed `gateway.pid` at `/home/hermes/.hermes/gateway.pid` for the single gateway service.

## ADDED Requirements

### Requirement: The managed gateway publishes a live `gateway.pid`
The repo-managed gateway service SHALL maintain a `gateway.pid` marker at the root managed Hermes home that matches the live managed gateway process used for Hermes health checks.

#### Scenario: Managed gateway start writes the current PID
- **WHEN** the managed gateway service starts
- **THEN** `/home/hermes/.hermes/gateway.pid` is created or replaced
- **AND** the file contains the PID of the long-running managed gateway process

#### Scenario: Managed gateway restart refreshes stale pidfiles
- **WHEN** the managed gateway service restarts or replaces an earlier process
- **THEN** any stale `gateway.pid` content from the earlier run is removed or overwritten
- **AND** the resulting `gateway.pid` points to the current managed gateway process rather than the previous run

### Requirement: Managed gateway liveness markers follow the service lifecycle
Repo-owned managed gateway marker files SHALL stay aligned with the managed service lifecycle so Hermes doctor/status surfaces do not report false negatives for the live repo-managed gateway.

#### Scenario: Live managed gateway is visible to Hermes health checks
- **WHEN** the repo-managed gateway process is running under the managed systemd service
- **THEN** the liveness marker exposes that gateway as running to Hermes doctor/status checks

#### Scenario: Stopped managed gateway does not leave misleading liveness state
- **WHEN** the managed gateway service stops cleanly
- **THEN** stale repo-owned liveness markers are removed or invalidated during the stop lifecycle
- **AND** later health checks do not report a stopped managed gateway as still live because of stale marker state
