## MODIFIED Requirements

### Requirement: Bootstrap projects generic Discord configuration into the managed `.env`
The Hermes image SHALL project the documented single-agent Discord runtime inputs into `/home/hermes/.hermes/.env` on every managed bootstrap run, using the current container env as the source of truth for the rewritten file.

#### Scenario: Generic Discord env are available during managed bootstrap
- **WHEN** `DISCORD_BOT_TOKEN`, `DISCORD_ALLOWED_USERS`, `GHOSTSHIP_ROUTER_CHANNEL`, or `DISCORD_HOME_CHANNEL` are present on the container during managed bootstrap
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
