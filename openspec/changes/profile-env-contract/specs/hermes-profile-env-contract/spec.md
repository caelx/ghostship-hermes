## MODIFIED Requirements

### Requirement: Managed profile `.env` is the operator-facing source of truth for profile runtime env
The Hermes image SHALL treat each managed profile `.env` file as the single operator-facing source of truth for supported profile-facing runtime configuration.

#### Scenario: Profile-facing env is written into managed profile `.env`
- **WHEN** bootstrap generates or refreshes the managed `assistant`, `operations`, and `supervisor` profiles
- **THEN** the generated profile `.env` contains the supported shared and profile-scoped profile-facing runtime env that is present on the container
- **AND** the generated profile `.env` omits supported keys that are unset on the container instead of inventing placeholder values
- **AND** long-running profile gateways continue to load their operator-facing runtime env from that profile `.env`

#### Scenario: Router-daemon and image-plumbing env stay outside managed profile `.env`
- **WHEN** bootstrap refreshes a managed profile `.env`
- **THEN** router-daemon variables and image/container plumbing variables are omitted from that profile `.env`
- **AND** the managed profile contract does not copy router service configuration into every profile simply because it exists on the container

### Requirement: Bootstrap projects the supported shared profile-facing env inventory into profile `.env`
The Hermes image SHALL project the full supported shared profile-facing runtime env inventory into each managed profile `.env` when those values are present on the container.

#### Scenario: Shared provider, browser, and workflow env are available during bootstrap
- **WHEN** supported shared profile-facing env are present on the container during managed bootstrap
- **THEN** each managed profile `.env` contains the matching shared profile-facing env values needed by that profile runtime
- **AND** the shared projection includes provider credentials, browser-provider configuration, Bitwarden access, Home Assistant access, GitHub workflow auth, supported custom-endpoint overrides, and the utility/service env needed by the installed `ghostship-*` CLIs and router-invoked utility calls

#### Scenario: Shared projection uses the approved allowlist instead of mirroring all container env
- **WHEN** bootstrap rewrites a managed profile `.env`
- **THEN** it copies only the approved shared profile-facing env allowlist into the file
- **AND** it does not mirror arbitrary unrelated container env into profile state

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

### Requirement: Bootstrap maps profile-specific browser CDP sources into profile-local browser env
The Hermes image SHALL treat remote browser CDP configuration as profile-scoped operator-facing runtime env and SHALL translate each profile-specific container env source into only that profile's local `BROWSER_CDP_URL`.

#### Scenario: Profile-specific browser CDP env are available during bootstrap
- **WHEN** `BROWSER_ASSISTANT_CDP_URL`, `BROWSER_OPERATIONS_CDP_URL`, or `BROWSER_SUPERVISOR_CDP_URL` are present on the container during managed bootstrap
- **THEN** bootstrap writes `BROWSER_CDP_URL` only into the matching managed profile `.env`
- **AND** bootstrap does not copy one profile's CDP target into another managed profile `.env`

#### Scenario: Missing profile-specific browser CDP env are omitted from rewritten managed `.env`
- **WHEN** a managed profile's source browser CDP env is absent during a bootstrap rewrite
- **THEN** bootstrap omits `BROWSER_CDP_URL` from that profile's rewritten `.env`
- **AND** the rewritten file does not preserve a stale profile CDP target from an earlier bootstrap run

### Requirement: Profile `.env` changes remain visible to service restart wiring
The Hermes image SHALL keep supported profile-facing env in the managed profile `.env` path so bootstrap rewrites and operator edits both remain the file-level change surface for the managed gateway restart wiring.

#### Scenario: Bootstrap rewrite stays on the watched `.env` path
- **WHEN** managed bootstrap refreshes a profile `.env` with changed supported profile-facing env
- **THEN** the rewrite occurs at the same managed profile `.env` path already watched by the repo-owned restart units
- **AND** the managed gateway continues to load its operator-facing runtime env from that `.env` path

#### Scenario: Managed gateway restart reads the rewritten `.env`
- **WHEN** a managed gateway is restarted after its profile `.env` changes
- **THEN** the restarted service reads the rewritten profile `.env` through the existing `EnvironmentFile` contract
- **AND** the runtime does not require hidden service-only env overrides to restore supported profile-facing configuration

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

### Requirement: Managed bootstrap rewrites profile `.env` idempotently
The Hermes image SHALL rewrite managed profile `.env` files only when the effective supported profile-facing content changes.

#### Scenario: Effective profile-facing env content is unchanged
- **WHEN** bootstrap renders the same effective managed profile `.env` content that is already present on disk
- **THEN** bootstrap leaves the existing file in place
- **AND** the managed runtime does not trigger a restart solely because bootstrap rewrote identical profile-facing env content
