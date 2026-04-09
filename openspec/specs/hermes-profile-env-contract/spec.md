## ADDED Requirements

### Requirement: Managed profile `.env` is the operator-facing source of truth for profile runtime env
The Hermes image SHALL treat each managed profile `.env` file as the single operator-facing source of truth for supported profile-facing runtime configuration.

#### Scenario: Profile-facing env is written into managed profile `.env`
- **WHEN** bootstrap generates or refreshes the managed `assistant`, `operations`, and `supervisor` profiles
- **THEN** the generated profile `.env` contains the supported shared profile-facing runtime env that is present on the container
- **AND** the generated profile `.env` omits supported keys that are unset on the container instead of inventing placeholder values
- **AND** long-running profile gateways continue to load their operator-facing runtime env from that profile `.env`

### Requirement: Bootstrap projects Discord configuration into profile `.env`
The Hermes image SHALL project the documented shared and per-profile Discord runtime inputs into the matching managed profile `.env` files when those values are present on the container.

#### Scenario: Shared and profile-specific Discord env are available
- **WHEN** `DISCORD_GENERAL_CHANNEL_ID` and one or more profile-specific Discord values are present on the container during bootstrap
- **THEN** bootstrap writes the corresponding Hermes-facing Discord env into each affected profile `.env`
- **AND** the shared mention-only channel is written as the shared home-channel setting
- **AND** each profile-specific bot token, allowed-user list, and free-response channel mapping is written only to that profile's `.env`

#### Scenario: Missing Discord values stay absent
- **WHEN** a profile-specific Discord value is not present on the container during bootstrap
- **THEN** bootstrap does not synthesize a replacement value in that profile `.env`
- **AND** the resulting profile `.env` still remains the operator-facing source of truth for what is actually configured

### Requirement: Profile `.env` changes remain visible to service restart wiring
The Hermes image SHALL keep supported profile-facing env in the managed profile `.env` path so the existing restart triggers continue to reflect operator-visible configuration changes.

#### Scenario: Projected `.env` changes trigger managed gateway refresh behavior
- **WHEN** bootstrap rewrites a managed profile `.env` with changed supported profile-facing env
- **THEN** the existing profile `.env` watch path remains the file-level change surface for the managed gateway restart wiring
- **AND** the runtime does not require a hidden service-only env override to pick up those profile-facing changes
