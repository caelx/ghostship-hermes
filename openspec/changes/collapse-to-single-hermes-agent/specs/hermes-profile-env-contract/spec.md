## REMOVED Requirements

### Requirement: Managed profile `.env` is the operator-facing source of truth for profile runtime env
**Reason**: The runtime no longer treats named profiles as the supported operator-facing env boundary.
**Migration**: Move the approved operator-facing env contract to one managed `.env` under `/home/hermes/.hermes`.

### Requirement: Bootstrap projects the supported shared profile-facing env inventory into profile `.env`
**Reason**: The approved allowlist now applies to one single-agent managed env file instead of duplicated profile files.
**Migration**: Project the same supported shared env inventory into the root managed `.env`.

### Requirement: Bootstrap projects Discord configuration into profile `.env`
**Reason**: Discord wiring is no longer profile-specific in the supported runtime topology.
**Migration**: Replace profile-specific source mapping with one single-agent Discord env contract and one managed `.env`.

### Requirement: Bootstrap maps profile-specific browser CDP sources into profile-local browser env
**Reason**: Browser CDP configuration is no longer profile-scoped in the supported runtime topology.
**Migration**: Replace `BROWSER_<PROFILE>_CDP_URL` source handling with one single-agent `BROWSER_CDP_URL` contract.

### Requirement: Profile `.env` changes remain visible to service restart wiring
**Reason**: Restart wiring now watches one managed env file for one gateway service.
**Migration**: Point the watched restart path at the single managed `.env`.

### Requirement: Bootstrap projects managed webhook listener env into profile `.env`
**Reason**: Webhook listener wiring is no longer duplicated per profile.
**Migration**: Project webhook listener inputs into the root managed `.env` for the single gateway.

### Requirement: Bootstrap maps profile-specific webhook secret sources into Hermes-facing env
**Reason**: Webhook secret projection is no longer profile-local in the supported runtime topology.
**Migration**: Replace profile-specific secret source vars with one single-agent webhook secret contract.

### Requirement: Managed bootstrap rewrites profile `.env` idempotently
**Reason**: Idempotent rewrites still matter, but the contract now applies to one managed `.env` file rather than profile-specific files.
**Migration**: Preserve idempotent rewrite behavior for `/home/hermes/.hermes/.env`.

## ADDED Requirements

### Requirement: Managed `.env` is the operator-facing source of truth for single-agent runtime env
The Hermes image SHALL treat the managed `.env` file at the root managed Hermes home as the single operator-facing source of truth for supported runtime configuration.

#### Scenario: Supported runtime env is written into the managed `.env`
- **WHEN** bootstrap generates or refreshes the managed runtime env
- **THEN** the generated `.env` contains the supported operator-facing runtime env that is present on the container
- **AND** the generated `.env` omits supported keys that are unset on the container instead of inventing placeholder values
- **AND** the long-running managed gateway continues to load its operator-facing runtime env from that `.env`

#### Scenario: Router-daemon and image-plumbing env stay outside the managed `.env`
- **WHEN** bootstrap refreshes the managed `.env`
- **THEN** router-daemon variables and image/container plumbing variables are omitted from that `.env`
- **AND** the managed env contract does not copy router service configuration into the agent runtime simply because it exists on the container

### Requirement: Bootstrap projects the supported shared runtime env inventory into the managed `.env`
The Hermes image SHALL project the full supported shared runtime env inventory into the managed `.env` when those values are present on the container.

#### Scenario: Shared provider, browser, and workflow env are available during bootstrap
- **WHEN** supported shared runtime env are present on the container during managed bootstrap
- **THEN** the managed `.env` contains the matching runtime env values needed by the single managed agent
- **AND** the shared projection includes provider credentials, browser-provider configuration, Bitwarden access, Home Assistant access, GitHub workflow auth, supported custom-endpoint overrides, and the utility/service env needed by the installed `ghostship-*` CLIs and router-invoked utility calls

#### Scenario: Shared projection uses the approved allowlist instead of mirroring all container env
- **WHEN** bootstrap rewrites the managed `.env`
- **THEN** it copies only the approved shared runtime env allowlist into the file
- **AND** it does not mirror arbitrary unrelated container env into managed state

### Requirement: Bootstrap projects Discord configuration into the managed `.env`
The Hermes image SHALL project the documented single-agent Discord runtime inputs into the managed `.env` on every managed bootstrap run, using the current container env as the source of truth for the rewritten file.

#### Scenario: Single-agent Discord env are available during managed bootstrap
- **WHEN** the supported Discord values are present on the container during managed bootstrap
- **THEN** bootstrap rewrites the managed `.env` with the corresponding Hermes-facing Discord env for the single managed agent
- **AND** the managed config sets Hermes Discord `auto_thread` to `false`
- **AND** the managed runtime does not create Discord threads automatically for the default single-agent channel by default

#### Scenario: Missing Discord values are removed from the rewritten managed `.env`
- **WHEN** a previously projected Discord value is no longer present on the container during a later managed bootstrap run
- **THEN** bootstrap omits that value from the rewritten managed `.env`
- **AND** the resulting file does not preserve a stale Discord value from an earlier bootstrap

### Requirement: Bootstrap projects browser CDP configuration into the managed `.env`
The Hermes image SHALL treat remote browser CDP configuration as a single-agent operator-facing runtime input and SHALL translate it into the managed `BROWSER_CDP_URL`.

#### Scenario: Browser CDP env is available during bootstrap
- **WHEN** `BROWSER_CDP_URL` is present on the container during managed bootstrap
- **THEN** bootstrap writes `BROWSER_CDP_URL` into the managed `.env`
- **AND** the runtime does not require profile-specific browser CDP source vars for the supported default workflow

#### Scenario: Missing browser CDP env is omitted from rewritten managed `.env`
- **WHEN** the source browser CDP env is absent during a bootstrap rewrite
- **THEN** bootstrap omits `BROWSER_CDP_URL` from the rewritten managed `.env`
- **AND** the rewritten file does not preserve a stale browser CDP target from an earlier bootstrap run

### Requirement: Bootstrap projects managed webhook listener env into the managed `.env`
The Hermes image SHALL project the managed webhook listener runtime inputs into the managed `.env` on every bootstrap rewrite.

#### Scenario: Managed bootstrap rewrites webhook env for the single agent
- **WHEN** bootstrap generates or refreshes the managed `.env`
- **THEN** the rewritten `.env` contains `WEBHOOK_ENABLED=true` when webhook support is part of the managed runtime contract
- **AND** the rewritten `.env` contains the assigned managed `WEBHOOK_PORT`
- **AND** the rewritten `.env` remains the `EnvironmentFile` source for the managed gateway service

#### Scenario: Managed bootstrap projects the webhook secret
- **WHEN** `WEBHOOK_SECRET` is present on the container during managed bootstrap
- **THEN** bootstrap writes `WEBHOOK_SECRET` into the managed `.env`
- **AND** the rewritten file does not preserve a stale `WEBHOOK_SECRET` from an earlier bootstrap run once the source env is absent

### Requirement: Managed bootstrap rewrites the managed `.env` idempotently
The Hermes image SHALL rewrite the managed `.env` file only when the effective supported runtime content changes.

#### Scenario: Effective managed env content is unchanged
- **WHEN** bootstrap renders the same effective managed `.env` content that is already present on disk
- **THEN** bootstrap leaves the existing file in place
- **AND** the managed runtime does not trigger a restart solely because bootstrap rewrote identical runtime env content
