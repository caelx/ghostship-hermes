## ADDED Requirements

### Requirement: Persisted home release marker mirrors the booted image release
The Hermes image SHALL refresh the persisted home-scoped release marker from the authoritative image release marker on every managed boot.

#### Scenario: Managed boot rewrites the persisted home release marker
- **WHEN** the image boots and managed runtime bootstrap prepares persisted `/home/hermes`
- **THEN** `/home/hermes/.ghostship-hermes-release` is rewritten from `/etc/ghostship-hermes-release`
- **AND** the resulting persisted marker matches the currently booted image release version

#### Scenario: Reused persisted home does not keep an older release marker
- **WHEN** `/home/hermes` is reused from an older deployment
- **THEN** the managed boot refreshes `/home/hermes/.ghostship-hermes-release` to the new image release value
- **AND** the persisted marker does not remain pinned to the older deployment's version string

### Requirement: Managed profile gateways publish a live `gateway.pid`
Each repo-managed profile gateway service SHALL maintain a `gateway.pid` marker that matches the live managed gateway process used for Hermes health checks.

#### Scenario: Managed gateway start writes the current PID
- **WHEN** a managed profile gateway service starts
- **THEN** the corresponding profile `gateway.pid` file is created or replaced
- **AND** the file contains the PID of the long-running managed gateway process for that profile

#### Scenario: Managed gateway restart refreshes stale pidfiles
- **WHEN** a managed profile gateway service restarts or replaces an earlier process
- **THEN** any stale `gateway.pid` content from the earlier run is removed or overwritten
- **AND** the resulting `gateway.pid` points to the current managed gateway process rather than the previous run

### Requirement: Managed gateway liveness markers follow the service lifecycle
Repo-owned managed gateway marker files SHALL stay aligned with the managed service lifecycle so Hermes doctor/status surfaces do not report false negatives for live repo-managed gateways.

#### Scenario: Live managed gateways are visible to Hermes health checks
- **WHEN** the repo-managed profile gateway process is running under the managed systemd service
- **THEN** the profile's liveness markers expose that gateway as running to Hermes doctor/status checks

#### Scenario: Stopped managed gateways do not leave misleading liveness state
- **WHEN** the managed profile gateway service stops cleanly
- **THEN** stale repo-owned liveness markers are removed or invalidated during the stop lifecycle
- **AND** later health checks do not report a stopped managed gateway as still live because of stale marker state
