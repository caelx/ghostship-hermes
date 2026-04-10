## ADDED Requirements

### Requirement: Managed profiles scaffold distinct webhook listeners
The Hermes image SHALL scaffold the managed `assistant`, `operations`, and `supervisor` profiles so each profile gateway runs with webhook support enabled on a distinct listener port.

#### Scenario: Managed profile config enables one listener per profile
- **WHEN** the image materializes or refreshes the managed `assistant`, `operations`, and `supervisor` profiles
- **THEN** each managed profile is configured to run the Hermes webhook adapter
- **AND** `assistant` uses webhook port `8644`
- **AND** `operations` uses webhook port `8645`
- **AND** `supervisor` uses webhook port `8646`

### Requirement: Managed profile gateways avoid webhook port conflicts
The Hermes image SHALL assign the managed profile webhook listeners so all three repo-owned profile gateway services can start concurrently without contending for the same webhook socket.

#### Scenario: All managed profile gateways start with webhook support enabled
- **WHEN** the repo-owned `assistant`, `operations`, and `supervisor` gateway services start on the same runtime instance
- **THEN** no two managed profiles are assigned the same webhook listener port
- **AND** the webhook listener contract does not require an operator to override ports before the default image runtime becomes valid

### Requirement: Managed profiles use profile-local webhook secrets
The Hermes image SHALL map a distinct deployment-provided webhook secret source to each managed profile so the running Hermes gateway process for that profile receives only its own webhook secret.

#### Scenario: Profile-specific webhook secrets are provided on the container
- **WHEN** the container provides `WEBHOOK_ASSISTANT_SECRET`, `WEBHOOK_OPERATIONS_SECRET`, and `WEBHOOK_SUPERVISOR_SECRET` during managed bootstrap
- **THEN** the managed `assistant` profile receives only the assistant webhook secret as its Hermes-facing `WEBHOOK_SECRET`
- **AND** the managed `operations` profile receives only the operations webhook secret as its Hermes-facing `WEBHOOK_SECRET`
- **AND** the managed `supervisor` profile receives only the supervisor webhook secret as its Hermes-facing `WEBHOOK_SECRET`
