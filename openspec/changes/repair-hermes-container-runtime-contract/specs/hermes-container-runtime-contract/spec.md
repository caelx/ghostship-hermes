## ADDED Requirements

### Requirement: Hermes container shutdown SHALL complete within the declared stop budget
The published `ghostship-hermes` container SHALL exit cleanly after `SIGTERM` within the configured container stop timeout during operator-driven restart and stop flows, instead of depending on Podman `SIGKILL` to terminate the runtime.

#### Scenario: Managed restart stops the live container without forced kill
- **WHEN** a maintainer or host unit restarts the live `ghostship-hermes` container with the repo-supported stop timeout
- **THEN** Podman reports that the container exited during the graceful stop window
- **AND** the host journal does not log that `SIGTERM` failed and `SIGKILL` was required

#### Scenario: Direct stop uses the same graceful shutdown contract
- **WHEN** an operator runs a direct `podman stop` against the live `ghostship-hermes` container with the declared stop budget
- **THEN** the container exits before the grace period expires
- **AND** the stop flow does not require Podman to escalate to `SIGKILL`

### Requirement: Hermes managed gateway stop semantics SHALL align with the graceful container shutdown path
The repo-owned managed `hermes-gateway.service` SHALL use stop behavior that is compatible with clean user-manager and container shutdown, including the upstream Hermes service expectations that materially affect signal delivery and stop ordering.

#### Scenario: Managed gateway service definition matches the intended stop contract
- **WHEN** maintainers inspect the rendered `hermes-gateway.service` inside the image
- **THEN** the unit exposes the intended kill mode, kill signal, and stop timeout fields for graceful shutdown
- **AND** those fields do not silently fall back to unrelated defaults that prolong container termination

#### Scenario: Gateway does not block user-manager shutdown past the stop budget
- **WHEN** the Hermes user manager is stopped during container shutdown
- **THEN** the managed gateway service exits within its configured stop timeout
- **AND** the user-manager stop path does not remain active until the container-level grace window is exhausted

### Requirement: Hermes container activation SHALL avoid known container-mode write failures
The published `ghostship-hermes` image SHALL boot without the current known activation defects around Podman-managed `/etc` files and root channel symlink creation.

#### Scenario: Stage-2 activation does not warn on Podman-managed `/etc` files
- **WHEN** the container boots under the supported Podman deployment
- **THEN** stage-2 activation does not emit the current symlink creation failures for `/etc/hostname` and `/etc/hosts`

#### Scenario: Boot does not try to create root channel links on a read-only path
- **WHEN** the container boots under the published image contract
- **THEN** activation does not attempt to create `/root/.nix-defexpr/channels/channels`
- **AND** the boot log does not contain the current read-only filesystem error for that path

### Requirement: Managed user-tooling convergence SHALL avoid full profile churn when state is current
The published `ghostship-hermes` image SHALL reconcile the managed user tooling layer incrementally so a normal boot does not remove and re-add every managed Nix profile entry or rerun the npm layer unnecessarily when the desired runtime toolchain is already present.

#### Scenario: Boot-time tooling convergence is a no-op when managed state already matches
- **WHEN** the managed user tooling profile and npm project already match the declared image-owned state on boot
- **THEN** `ghostship-hermes-user-tooling.service` does not remove and re-add each managed profile package one by one
- **AND** the service does not rerun npm dependency installation solely because the container restarted

#### Scenario: Boot-time tooling convergence still repairs drifted managed entries
- **WHEN** one or more managed tooling entries drift from the declared runtime contract
- **THEN** `ghostship-hermes-user-tooling.service` updates only the entries that differ
- **AND** the resulting managed profile and `.local/bin` links converge back to the declared image-owned state
