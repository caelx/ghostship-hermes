## MODIFIED Requirements

### Requirement: Hermes seeds a repo-managed Bitwarden skill
The default Hermes skill inventory SHALL include a repo-managed Bitwarden skill that is copied into `~/.hermes/skills` on first start without overwriting an existing user-managed skill directory of the same name.

#### Scenario: Fresh Hermes profile receives the Bitwarden skill
- **WHEN** a fresh Hermes profile receives the default seeded skill tree
- **THEN** the seeded skills include the repo-managed Bitwarden skill
- **AND** the skill content describes the supported Bitwarden Secrets Manager workflow

#### Scenario: Existing Bitwarden skill is preserved
- **WHEN** a Bitwarden skill directory already exists in `~/.hermes/skills`
- **THEN** runtime skill seeding leaves the existing directory unchanged

### Requirement: Bitwarden skill defines the official stateless auth workflow
The repo-managed Bitwarden skill SHALL instruct agents to use Bitwarden Secrets Manager's official access-token-driven workflow and SHALL not depend on Password Manager login, vault unlock, or `BW_SESSION`.

#### Scenario: Skill documents the required environment variables
- **WHEN** maintainers inspect the Bitwarden skill content
- **THEN** the skill names `BWS_ACCESS_TOKEN`
- **AND** the skill explains the repo-defined Hermes-managed `bws` configuration/state path

#### Scenario: Skill documents noninteractive secrets-manager auth
- **WHEN** maintainers inspect the Bitwarden skill content
- **THEN** the skill directs agents to authenticate with the official `bws` access-token workflow
- **AND** the skill explicitly avoids `bw login`, `bw unlock`, and `BW_SESSION` as supported guidance

### Requirement: Bitwarden skill covers shared secret retrieval conventions
The repo-managed Bitwarden skill SHALL describe how agents receive operator-managed credentials through Bitwarden Secrets Manager machine-account access and retrieve project-scoped secrets with the official CLI.

#### Scenario: Skill covers machine-account usage
- **WHEN** maintainers inspect the Bitwarden skill content
- **THEN** the skill explains that the agent should use an operator-managed Secrets Manager machine account or equivalent access-token workflow
- **AND** the skill describes project-scoped secrets as the supported sharing model

#### Scenario: Skill covers JSON-friendly secret retrieval
- **WHEN** maintainers inspect the Bitwarden skill content
- **THEN** the skill directs agents to use `bws` retrieval commands that return structured secret data suitable for downstream scripting
- **AND** the skill describes changedetection credentials as a concrete service-secret workflow
