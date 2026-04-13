## ADDED Requirements

### Requirement: Host-managed Podman deployment preserves the supported container stop contract
The deployment SHALL run the Hermes container with host-side Podman and systemd settings that preserve the image's supported shutdown behavior instead of reporting a clean signaled stop as a failed service.

#### Scenario: `systemctl stop` ends cleanly without a failed unit result
- **WHEN** an operator runs `systemctl stop podman-hermes.service` against a healthy Hermes deployment
- **THEN** the container stops through the supported signal path without Podman escalating to `SIGKILL`
- **AND** `podman-hermes.service` does not remain in `failed` state solely because Podman exits with the expected status for a clean signaled stop

#### Scenario: `systemctl restart` reuses the clean stop path
- **WHEN** an operator runs `systemctl restart podman-hermes.service`
- **THEN** the old Hermes container stops through the supported signal path without a forced-kill warning
- **AND** the replacement container starts afterward under the same supported runtime contract

### Requirement: Host runtime wiring must not conflict with the image-managed hostname contract
The deployment SHALL avoid injecting a host-managed `/etc/hostname` view that conflicts with the image's explicit `ghostship-hermes` hostname contract.

#### Scenario: Boot does not log a conflicting `/etc/hostname` setup warning
- **WHEN** the Hermes container boots under the supported deployment contract
- **THEN** stage-2 does not log a `could not create symlink /etc/hostname` warning caused by conflicting host runtime file injection
- **AND** the running container still reports the supported image-managed hostname contract

### Requirement: Container boot must not expose stale root channel state
The Hermes image SHALL not ship or regenerate contradictory root-channel state that causes stage-2 boot warnings in the supported container runtime.

#### Scenario: Boot does not warn about disabled-but-present root channels
- **WHEN** the Hermes container boots under the supported runtime contract
- **THEN** stage-2 does not warn that `/nix/var/nix/profiles/per-user/root/channels` exists while channels are disabled
- **AND** the boot does not attempt to create `/root/.nix-defexpr/channels/channels` on a read-only filesystem

### Requirement: Deployment validation proves the runtime contract directly
The repo SHALL require deployment validation that inspects the running host service and latest boot window instead of assuming the intended runtime contract reached the live artifact.

#### Scenario: Validation checks stop semantics and activation cleanliness on the deployed host
- **WHEN** maintainers validate a newly deployed Hermes image
- **THEN** the validation checks at least one `systemctl stop` or `restart` path on the host-managed unit
- **AND** the validation checks the latest boot logs for the supported hostname and root-channel cleanliness expectations
- **AND** the deployment is not treated as healthy if those host-level checks fail
