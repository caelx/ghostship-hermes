## ADDED Requirements

### Requirement: Managed profile `.env` is the operator-facing source of truth for profile runtime env
The Hermes image SHALL treat each managed profile `.env` file as the single operator-facing source of truth for supported profile-facing runtime configuration.

#### Scenario: Profile-facing env is written into managed profile `.env`
- **WHEN** bootstrap generates or refreshes the managed `assistant`, `operations`, and `supervisor` profiles
- **THEN** the generated profile `.env` contains the supported shared profile-facing runtime env that is present on the container
- **AND** the generated profile `.env` omits supported keys that are unset on the container instead of inventing placeholder values
- **AND** long-running profile gateways continue to load their operator-facing runtime env from that profile `.env`

### Requirement: Bootstrap projects Discord configuration into profile `.env`
The Hermes image SHALL project the documented shared and per-profile Discord runtime inputs into the matching managed profile `.env` files on every managed bootstrap run, using the current container env as the source of truth for the rewritten file.

#### Scenario: Shared and profile-specific Discord env are available during managed bootstrap
- **WHEN** `DISCORD_GENERAL_CHANNEL_ID` and one or more profile-specific Discord values are present on the container during managed bootstrap
- **THEN** bootstrap rewrites each affected managed profile `.env` with the corresponding Hermes-facing Discord env for that profile
- **AND** the shared mention-only channel is written as the shared home-channel setting
- **AND** each profile-specific bot token, allowed-user list, and free-response channel mapping is written only to that profile's `.env`

#### Scenario: Managed Discord scaffold disables automatic thread creation
- **WHEN** bootstrap materializes or refreshes the managed `assistant`, `operations`, and `supervisor` profile config
- **THEN** each managed profile sets Hermes Discord `auto_thread` to `false`
- **AND** the managed runtime does not create Discord threads automatically for any managed profile channel by default

#### Scenario: Missing Discord values are removed from the rewritten managed `.env`
- **WHEN** a previously projected profile-specific Discord value is no longer present on the container during a later managed bootstrap run
- **THEN** bootstrap omits that value from the rewritten profile `.env`
- **AND** the resulting `.env` does not preserve a stale Discord value from an earlier bootstrap

### Requirement: Profile `.env` changes remain visible to service restart wiring
The Hermes image SHALL keep supported profile-facing env in the managed profile `.env` path so bootstrap rewrites and operator edits both remain the file-level change surface for the managed gateway restart wiring.

#### Scenario: Bootstrap rewrite stays on the watched `.env` path
- **WHEN** managed bootstrap refreshes a profile `.env` with changed supported profile-facing env
- **THEN** the rewrite occurs at the same managed profile `.env` path already watched by the repo-owned restart units
- **AND** the managed gateway continues to load its operator-facing runtime env from that `.env` path

#### Scenario: Managed gateway restart reads the rewritten `.env`
- **WHEN** a managed gateway is restarted after its profile `.env` changes
- **THEN** the restarted service reads the rewritten profile `.env` through the existing `EnvironmentFile` contract
- **AND** the runtime does not require a hidden service-only Discord env override to restore messaging configuration

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
