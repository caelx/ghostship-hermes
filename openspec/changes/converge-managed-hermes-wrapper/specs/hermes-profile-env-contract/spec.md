## MODIFIED Requirements

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
