## REMOVED Requirements

### Requirement: Managed profiles scaffold distinct webhook listeners
**Reason**: The runtime no longer starts concurrent profile-specific gateways that need independent webhook listeners.
**Migration**: Replace the per-profile listener matrix with one managed webhook listener contract for the single agent.

### Requirement: Managed profile gateways avoid webhook port conflicts
**Reason**: Port-conflict avoidance between concurrent named profile gateways is no longer part of the supported topology.
**Migration**: Validate one managed webhook listener port for the single gateway service.

### Requirement: Managed profiles use profile-local webhook secrets
**Reason**: The runtime no longer projects distinct webhook secrets into separate profile homes.
**Migration**: Replace the profile-local secret mapping with one managed `WEBHOOK_SECRET` contract.

## ADDED Requirements

### Requirement: Managed runtime scaffolds one webhook listener for the single agent
The Hermes image SHALL scaffold the single managed agent so the managed gateway can run the Hermes webhook adapter on one repo-owned listener port.

#### Scenario: Managed runtime config enables one listener
- **WHEN** the image materializes or refreshes the managed single-agent config
- **THEN** the managed runtime is configured to run the Hermes webhook adapter
- **AND** the managed `.env` exposes one assigned `WEBHOOK_PORT`
- **AND** the default image runtime does not require operators to assign multiple ports before webhook support becomes valid

### Requirement: Managed runtime uses one webhook secret for the single agent
The Hermes image SHALL map one deployment-provided webhook secret source into the managed runtime so the running Hermes gateway process receives the correct Hermes-facing `WEBHOOK_SECRET`.

#### Scenario: Webhook secret is provided on the container
- **WHEN** the container provides `WEBHOOK_SECRET` during managed bootstrap
- **THEN** the managed `.env` receives that webhook secret as its Hermes-facing `WEBHOOK_SECRET`
- **AND** the runtime does not require profile-specific secret source vars for the supported default workflow
