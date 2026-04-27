## MODIFIED Requirements

### Requirement: Managed agent `.env` is the operator-facing source of truth for runtime env
The workstation SHALL project the supported Hermes-facing runtime env inventory into both `/run/ghostship/hermes.env` and `/home/hermes/.hermes/.env` on boot, while preserving unrelated existing keys in the persisted home-state file.

#### Scenario: Existing non-managed `.env` keys survive restart
- **WHEN** `/home/hermes/.hermes/.env` already exists in the persisted home volume
- **THEN** workstation startup preserves any existing keys that are outside the managed Hermes env inventory
- **AND** the runtime refreshes managed keys from the current container env

#### Scenario: Missing `.env` is synthesized from the current runtime env
- **WHEN** `/home/hermes/.hermes/.env` is absent at startup
- **THEN** the runtime generates a persisted `/home/hermes/.hermes/.env` from the managed Hermes env inventory
- **AND** the generated file matches the live Hermes-facing env contract apart from any preserved downstream-only keys

#### Scenario: Managed keys removed from runtime env are removed from the persisted managed subset
- **WHEN** a key that was previously projected into `/home/hermes/.hermes/.env` is absent from the current supported runtime env
- **THEN** workstation startup removes that key from the managed subset of `/home/hermes/.hermes/.env`
- **AND** unrelated preserved keys remain intact

### Requirement: Managed `.env` changes remain visible to service restart wiring
The workstation SHALL keep operator-facing runtime env changes visible through both the live service env file and the persisted home-state env file generated at boot.

#### Scenario: Service runtime sees downstream-owned env changes
- **WHEN** the operator updates supported runtime env through the documented downstream mechanism
- **THEN** the affected services read the updated values from `/run/ghostship/hermes.env`
- **AND** the same managed values are projected into `/home/hermes/.hermes/.env`
- **AND** the runtime does not require operators to hand-edit both locations to keep them aligned

## REMOVED Requirements

### Requirement: Managed `.env` remains purely downstream-owned and never repo-generated
**Reason**: The workstation now emits the managed Hermes env inventory to the persisted home-state `.env` as well as the live service env file.
**Migration**: Downstream deployments SHALL keep supplying supported runtime env through Compose, `docker run`, or env files; the image now persists those supported keys into `/home/hermes/.hermes/.env` automatically.

## ADDED Requirements

### Requirement: Image-owned fixed path env are documented and set explicitly
The workstation image SHALL set and document the fixed filesystem/process env needed for the supported runtime layout.

#### Scenario: Runtime docs list the fixed path env
- **WHEN** maintainers inspect the runtime deployment docs
- **THEN** the docs list the image-owned fixed env such as `HOME`, `HERMES_HOME`, the XDG paths, `NPM_CONFIG_PREFIX`, and the supported `PATH` layout
- **AND** those documented values align with the actual image runtime configuration

### Requirement: Downstream docs define the supported operator-facing env inventory
The workstation docs SHALL enumerate the supported downstream-owned operator env inventory and how to supply it for the new container contract.

#### Scenario: Operator follows the env documentation
- **WHEN** a downstream operator reads the deployment guidance for the workstation image
- **THEN** the docs identify which env values are downstream-owned
- **AND** the docs show how to provide those values through Compose, `docker run`, or a persisted operator-managed env file under `/home/hermes/.hermes`
- **AND** the docs distinguish operator-facing env from image-internal plumbing env
- **AND** the docs identify `DISCORD_HOME_CHANNEL` as required downstream env for `#assistant` when the Discord gateway is enabled
- **AND** the docs identify `GHOSTSHIP_CODEX_CHANNEL` as the downstream-owned Discord channel pin env for `#foodstamps`
- **AND** the docs identify `DISCORD_FREE_RESPONSE_CHANNELS` as including the `#foodstamps` channel id
- **AND** the docs identify `DISCORD_WEBHOOK_CHANNEL` as the downstream-owned Discord webhook destination env for `#webhooks`
- **AND** the docs do not require the retired router-channel env as part of the Discord channel contract
- **AND** the docs explain that Codex auth remains persisted home state rather than a downstream env key

### Requirement: Managed Discord defaults use threaded daily sessions
The workstation SHALL configure managed Hermes Discord sessions to use threads by default and daily session reset at 04:00 local Hermes time.

#### Scenario: Managed config renders Discord thread and daily reset defaults
- **WHEN** the image materializes or reconciles the managed Hermes config
- **THEN** `discord.auto_thread` is `true`
- **AND** `session_reset.mode` is `daily`
- **AND** `session_reset.at_hour` is `4`

### Requirement: Default local browser runtime does not depend on operator-facing browser-service env
The workstation SHALL keep the supported default local browser path image-owned and SHALL NOT require downstream operators to supply Camofox or CloakBrowser Manager env to use the native local browser runtime.

#### Scenario: Supported local browser path works without browser-service env
- **WHEN** a downstream operator deploys the workstation image without `CAMOFOX_URL`, `CLOAKBROWSER_URL`, or `CLOAKBROWSER_TOKEN`
- **THEN** the supported default local browser path remains available
- **AND** the image does not require those env values for the supported stock `agent-browser` plus CloakBrowser workflow

#### Scenario: Manual CDP attachment remains a separate concern
- **WHEN** maintainers inspect the supported browser env inventory
- **THEN** the optional `BROWSER_CDP_URL` contract remains distinct from the supported default local browser path
- **AND** the supported default local browser path does not require operators to provide a CDP target

### Requirement: Browser plumbing env are documented as image-internal when retained
The workstation docs SHALL treat any retained browser-launch plumbing env for the supported default local browser path as image-internal rather than downstream-owned runtime knobs.

#### Scenario: Operator docs exclude retired browser-service env
- **WHEN** a downstream operator reads the documented runtime env inventory
- **THEN** the docs do not describe `CAMOFOX_URL`, `CLOAKBROWSER_URL`, or `CLOAKBROWSER_TOKEN` as supported downstream env for the workstation browser contract

#### Scenario: Internal browser-launch env are not exposed as supported knobs
- **WHEN** maintainers document the supported default local browser path
- **THEN** any image-owned browser-launch settings used to point `agent-browser` at CloakBrowser are described as internal image plumbing
- **AND** the docs do not tell downstream operators to override those internal settings for the supported path
