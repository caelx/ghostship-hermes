## MODIFIED Requirements

### Requirement: Managed agent `.env` is the operator-facing source of truth for runtime env
The Hermes image SHALL treat the managed agent `.env` at `/home/hermes/.hermes/.env` as the single operator-facing source of truth for supported runtime configuration.

#### Scenario: Agent-facing env is written into the managed `.env`
- **WHEN** bootstrap generates or refreshes the managed runtime
- **THEN** the generated `.env` contains the supported agent-facing runtime env that is present on the container
- **AND** the generated `.env` omits supported keys that are unset on the container instead of inventing placeholder values
- **AND** the long-running managed gateway continues to load its operator-facing runtime env from that `.env`

#### Scenario: Router-daemon and image-plumbing env stay outside the managed `.env`
- **WHEN** bootstrap refreshes the managed `.env`
- **THEN** router-daemon variables and image/container plumbing variables are omitted from that `.env`
- **AND** the managed runtime contract does not copy router service configuration into Hermes state simply because it exists on the container

### Requirement: Bootstrap projects the supported runtime env inventory into the managed `.env`
The Hermes image SHALL project the full supported agent-facing runtime env inventory into `/home/hermes/.hermes/.env` when those values are present on the container.

#### Scenario: Provider, browser, and workflow env are available during bootstrap
- **WHEN** supported agent-facing env are present on the container during managed bootstrap
- **THEN** the managed `.env` contains the matching runtime env values needed by the managed agent
- **AND** the shared projection includes provider credentials, browser-provider configuration, Bitwarden access, supported custom-endpoint overrides, and the utility/service env needed by the installed `ghostship-*` CLIs and router-invoked utility calls

#### Scenario: Shared projection uses the approved allowlist instead of mirroring all container env
- **WHEN** bootstrap rewrites the managed `.env`
- **THEN** it copies only the approved agent-facing env allowlist into the file
- **AND** it does not mirror arbitrary unrelated container env into managed runtime state

### Requirement: Bootstrap projects generic Discord configuration into the managed `.env`
The Hermes image SHALL project the documented single-agent Discord runtime inputs into `/home/hermes/.hermes/.env` on every managed bootstrap run, using the current container env as the source of truth for the rewritten file.

#### Scenario: Generic Discord env are available during managed bootstrap
- **WHEN** `DISCORD_BOT_TOKEN`, `DISCORD_ALLOWED_USERS`, `DISCORD_FREE_RESPONSE_CHANNELS`, or `DISCORD_HOME_CHANNEL` are present on the container during managed bootstrap
- **THEN** bootstrap rewrites the managed `.env` with the matching Hermes-facing Discord env names
- **AND** the managed runtime does not perform any profile-specific Discord env translation

#### Scenario: Managed Discord scaffold disables automatic thread creation
- **WHEN** bootstrap materializes or refreshes the managed agent config
- **THEN** the managed config sets Hermes Discord `auto_thread` to `false`
- **AND** the managed runtime does not create Discord threads automatically by default

#### Scenario: Missing Discord values are removed from the rewritten managed `.env`
- **WHEN** a previously projected Discord value is no longer present on the container during a later managed bootstrap run
- **THEN** bootstrap omits that value from the rewritten managed `.env`
- **AND** the resulting `.env` does not preserve a stale Discord value from an earlier bootstrap

### Requirement: Bootstrap projects browser CDP configuration into the managed `.env`
The Hermes image SHALL treat remote browser CDP configuration as single-agent operator-facing runtime env and SHALL translate the deployment-provided container env source directly into `BROWSER_CDP_URL` in `/home/hermes/.hermes/.env`.

#### Scenario: Browser CDP env is available during bootstrap
- **WHEN** `BROWSER_CDP_URL` is present on the container during managed bootstrap
- **THEN** bootstrap writes `BROWSER_CDP_URL` into the managed `.env`
- **AND** the managed runtime does not keep any profile-local browser CDP contract

#### Scenario: Missing browser CDP env is omitted from rewritten managed `.env`
- **WHEN** `BROWSER_CDP_URL` is absent during a bootstrap rewrite
- **THEN** bootstrap omits `BROWSER_CDP_URL` from the rewritten managed `.env`
- **AND** the rewritten file does not preserve a stale browser CDP target from an earlier bootstrap run

### Requirement: Managed `.env` changes remain visible to service restart wiring
The Hermes image SHALL keep supported runtime env in `/home/hermes/.hermes/.env` so bootstrap rewrites and operator edits both remain the file-level change surface for the managed gateway restart wiring.

#### Scenario: Bootstrap rewrite stays on the watched `.env` path
- **WHEN** managed bootstrap refreshes `/home/hermes/.hermes/.env` with changed supported runtime env
- **THEN** the rewrite occurs at the same managed `.env` path already watched by the repo-owned restart unit
- **AND** the managed gateway continues to load its operator-facing runtime env from that `.env` path

#### Scenario: Managed gateway restart reads the rewritten `.env`
- **WHEN** the managed gateway is restarted after `/home/hermes/.hermes/.env` changes
- **THEN** the restarted service reads the rewritten managed `.env` through the existing `EnvironmentFile` contract
- **AND** the runtime does not require hidden service-only env overrides to restore supported configuration

### Requirement: Bootstrap projects managed webhook listener env into the managed `.env`
The Hermes image SHALL project the managed webhook listener runtime inputs into `/home/hermes/.hermes/.env` on every bootstrap rewrite.

#### Scenario: Managed bootstrap rewrites webhook env for the managed runtime
- **WHEN** bootstrap generates or refreshes the managed `.env`
- **THEN** the rewritten managed `.env` contains `WEBHOOK_ENABLED=true`
- **AND** the rewritten managed `.env` contains `WEBHOOK_PORT=8644`
- **AND** the rewritten managed `.env` remains the `EnvironmentFile` source for the managed gateway service

### Requirement: Bootstrap maps the deployment webhook secret source into Hermes-facing env
The Hermes image SHALL translate the deployment-provided `WEBHOOK_SECRET` source env name into the Hermes-facing `WEBHOOK_SECRET` expected by the managed gateway.

#### Scenario: Webhook secret source env is available during bootstrap
- **WHEN** `WEBHOOK_SECRET` is present on the container during managed bootstrap
- **THEN** bootstrap writes `WEBHOOK_SECRET` into the managed `.env`
- **AND** the managed runtime does not keep any profile-specific webhook secret contract

#### Scenario: Missing webhook secret source env is omitted from rewritten managed `.env`
- **WHEN** `WEBHOOK_SECRET` is absent during a bootstrap rewrite
- **THEN** bootstrap omits `WEBHOOK_SECRET` from the rewritten managed `.env`
- **AND** the rewritten file does not preserve a stale `WEBHOOK_SECRET` from an earlier bootstrap run

### Requirement: Managed bootstrap rewrites the managed `.env` idempotently
The Hermes image SHALL rewrite `/home/hermes/.hermes/.env` only when the effective supported agent-facing content changes.

#### Scenario: Effective agent-facing env content is unchanged
- **WHEN** bootstrap renders the same effective managed `.env` content that is already present on disk
- **THEN** bootstrap leaves the existing file in place
- **AND** the managed runtime does not trigger a restart solely because bootstrap rewrote identical agent-facing env content
