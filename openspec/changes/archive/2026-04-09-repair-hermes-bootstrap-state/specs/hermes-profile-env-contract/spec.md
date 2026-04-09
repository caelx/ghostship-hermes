## MODIFIED Requirements

### Requirement: Bootstrap projects Discord configuration into profile `.env`
The Hermes image SHALL project the documented shared and per-profile Discord runtime inputs into the matching managed profile `.env` files on every managed bootstrap run, using the current container env as the source of truth for the rewritten file.

#### Scenario: Shared and profile-specific Discord env are available during managed bootstrap
- **WHEN** `DISCORD_GENERAL_CHANNEL_ID` and one or more profile-specific Discord values are present on the container during managed bootstrap
- **THEN** bootstrap rewrites each affected managed profile `.env` with the corresponding Hermes-facing Discord env for that profile
- **AND** the shared mention-only channel is written as the shared home-channel setting
- **AND** each profile-specific bot token, allowed-user list, and free-response channel mapping is written only to that profile's `.env`

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
