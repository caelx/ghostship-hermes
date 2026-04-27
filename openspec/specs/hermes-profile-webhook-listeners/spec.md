## MODIFIED Requirements

### Requirement: Managed agent scaffolds one webhook listener
The Hermes image SHALL scaffold the managed runtime so the managed gateway runs with webhook support enabled on one authoritative listener port.

#### Scenario: Managed config enables the webhook listener
- **WHEN** the image materializes or refreshes the managed agent config
- **THEN** the managed runtime is configured to run the Hermes webhook adapter
- **AND** the managed runtime uses webhook port `8644`

### Requirement: Managed gateway avoids webhook port conflicts
The Hermes image SHALL assign the managed webhook listener so the repo-owned managed gateway service can start without contending for an unexpected alternate webhook socket.

#### Scenario: Managed gateway starts with webhook support enabled
- **WHEN** the repo-owned managed gateway service starts on the runtime instance
- **THEN** the managed runtime uses only the configured webhook listener port `8644`
- **AND** the webhook listener contract does not require an operator to override ports before the default image runtime becomes valid

### Requirement: Managed agent uses the deployment-provided webhook secret
The Hermes image SHALL map the deployment-provided webhook secret source to the managed runtime so the running Hermes gateway process receives the expected Hermes-facing secret.

#### Scenario: Webhook secret is provided on the container
- **WHEN** the container provides `WEBHOOK_SECRET` during managed bootstrap
- **THEN** the managed `.env` receives `WEBHOOK_SECRET`
- **AND** the managed gateway loads that secret through the managed runtime env contract

### Requirement: Discord webhook subscriptions default to the managed webhook channel
The Hermes image SHALL support `DISCORD_WEBHOOK_CHANNEL` as the default Discord delivery destination for Hermes-created webhook subscriptions.

#### Scenario: Discord delivery omits explicit chat id
- **WHEN** an operator runs `hermes webhook subscribe --deliver discord` without `--deliver-chat-id`
- **AND** `DISCORD_WEBHOOK_CHANNEL` is set in the managed runtime env
- **THEN** the created subscription stores that value as `deliver_extra.chat_id`

#### Scenario: Explicit Discord delivery chat id wins
- **WHEN** an operator runs `hermes webhook subscribe --deliver discord --deliver-chat-id <channel-id>`
- **AND** `DISCORD_WEBHOOK_CHANNEL` is also set
- **THEN** the created subscription stores the explicit `--deliver-chat-id` value as `deliver_extra.chat_id`
