## ADDED Requirements

### Requirement: Bootstrap projects managed webhook listener env into profile `.env`
The Hermes image SHALL project the managed webhook listener runtime inputs into each managed profile `.env` on every bootstrap rewrite.

#### Scenario: Managed bootstrap rewrites webhook env for all managed profiles
- **WHEN** bootstrap generates or refreshes the managed `assistant`, `operations`, and `supervisor` profile `.env` files
- **THEN** each rewritten profile `.env` contains `WEBHOOK_ENABLED=true`
- **AND** each rewritten profile `.env` contains that profile's assigned `WEBHOOK_PORT`
- **AND** each rewritten profile `.env` remains the `EnvironmentFile` source for the matching managed gateway service

### Requirement: Bootstrap maps profile-specific webhook secret sources into Hermes-facing env
The Hermes image SHALL translate the repo-owned profile-specific webhook secret source env names into the Hermes-facing `WEBHOOK_SECRET` expected by each managed profile gateway.

#### Scenario: Profile-specific webhook secret source env are available during bootstrap
- **WHEN** `WEBHOOK_ASSISTANT_SECRET`, `WEBHOOK_OPERATIONS_SECRET`, or `WEBHOOK_SUPERVISOR_SECRET` are present on the container during managed bootstrap
- **THEN** bootstrap writes `WEBHOOK_SECRET` only into the matching profile `.env`
- **AND** bootstrap does not copy one profile's webhook secret into another managed profile `.env`

#### Scenario: Missing webhook secret source env are omitted from rewritten managed `.env`
- **WHEN** a managed profile's source webhook secret env is absent during a bootstrap rewrite
- **THEN** bootstrap omits `WEBHOOK_SECRET` from that profile's rewritten `.env`
- **AND** the rewritten file does not preserve a stale `WEBHOOK_SECRET` from an earlier bootstrap run
