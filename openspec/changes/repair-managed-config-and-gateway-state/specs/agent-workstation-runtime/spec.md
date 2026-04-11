## MODIFIED Requirements

### Requirement: Image replacement converges repo-managed persisted system config
The workstation SHALL reconcile repo-owned persisted runtime config that is meant to track the current image generation during managed convergence, and it SHALL remove retired repo-owned keys that would otherwise shadow the current contract after image replacement.

#### Scenario: Image replacement converges the current managed config contract
- **WHEN** the workstation boots after replacing the image while repo-managed system config persists under `/home/hermes`
- **THEN** repo-owned persisted runtime config that is meant to track the current image generation is reconciled to the current contract during managed convergence
- **AND** stale persisted repo-managed values do not continue shadowing newer baked or bootstrap-defined runtime behavior from the replacement image

#### Scenario: Retired router-primary key does not survive replacement
- **WHEN** the current image contract no longer owns `model.base_url` for the root managed agent and persisted config still contains the older router-primary value
- **THEN** managed convergence removes that retired repo-owned key during boot
- **AND** the resulting managed config no longer routes the direct primary lane through the local router

### Requirement: Managed gateway commands align with upstream Hermes user services
The workstation SHALL align interactive gateway commands with upstream Hermes Linux service behavior by using a real `systemd --user` `hermes-gateway.service` owned by `hermes` instead of a repo-owned system unit or an upstream named-profile fleet.

#### Scenario: Managed gateway status reflects the upstream Hermes user unit
- **WHEN** an operator runs `hermes gateway status` or an equivalent Hermes status surface inside the managed image
- **THEN** the command reports the state of `systemd --user` `hermes-gateway.service`
- **AND** it does not claim the gateway is stopped solely because the image uses a repo-specific system-unit layout

#### Scenario: Managed control paths target the upstream Hermes user unit
- **WHEN** an operator runs `hermes gateway start`, `stop`, or `restart` inside the managed image
- **THEN** the command targets `systemd --user` `hermes-gateway.service` or equivalent upstream Hermes control behavior
- **AND** it does not redirect the operator to a Ghostship-specific system-unit contract

#### Scenario: Managed gateway starts without interactive login
- **WHEN** the container boots the managed runtime without an interactive Hermes login session
- **THEN** the Hermes user manager is available for `hermes-gateway.service`
- **AND** the managed gateway can start and restart through that user-service topology during normal boot
