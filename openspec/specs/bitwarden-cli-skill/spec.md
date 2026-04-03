# bitwarden-cli-skill Specification

## Purpose
TBD - created by archiving change add-bitwarden-cli-runtime-and-skill. Update Purpose after archive.
## Requirements
### Requirement: Hermes seeds a repo-managed Bitwarden skill
The default Hermes skill inventory SHALL include a repo-managed Bitwarden skill that is copied into `~/.hermes/skills` on first start without overwriting an existing user-managed skill directory of the same name.

#### Scenario: Fresh Hermes profile receives the Bitwarden skill
- **WHEN** a fresh Hermes profile receives the default seeded skill tree
- **THEN** the seeded skills include the repo-managed Bitwarden skill

#### Scenario: Existing Bitwarden skill is preserved
- **WHEN** a Bitwarden skill directory already exists in `~/.hermes/skills`
- **THEN** runtime skill seeding leaves the existing directory unchanged

### Requirement: Bitwarden skill defines the official stateless auth workflow
The repo-managed Bitwarden skill SHALL instruct agents to use Bitwarden's official environment-variable-driven flow with API-key login, password-based unlock, and ephemeral session export.

#### Scenario: Skill documents the required environment variables
- **WHEN** maintainers inspect the Bitwarden skill content
- **THEN** the skill names `BW_CLIENTID`, `BW_CLIENTSECRET`, `BW_PASSWORD`, `BITWARDENCLI_APPDATA_DIR`, and `BW_SESSION`
- **AND** the skill explains how each variable participates in the official `bw` workflow

#### Scenario: Skill documents noninteractive login and unlock
- **WHEN** maintainers inspect the Bitwarden skill content
- **THEN** the skill directs agents to use `bw login --apikey`
- **AND** the skill directs agents to derive `BW_SESSION` from `bw unlock --passwordenv BW_PASSWORD --raw`

### Requirement: Bitwarden skill covers shared secret retrieval conventions
The repo-managed Bitwarden skill SHALL describe how agents receive operator-shared credentials through a dedicated Bitwarden account and retrieve them with the official CLI.

#### Scenario: Skill covers shared account usage
- **WHEN** maintainers inspect the Bitwarden skill content
- **THEN** the skill explains that the agent should use a dedicated Bitwarden account that receives shared credentials from the operator
- **AND** the skill describes shared collections or equivalent supported sharing primitives as the expected sharing model

#### Scenario: Skill covers sync-before-read retrieval
- **WHEN** maintainers inspect the Bitwarden skill content
- **THEN** the skill tells agents to run `bw sync` before retrieving newly shared credentials
- **AND** the skill prefers JSON-friendly retrieval patterns for downstream scripting

