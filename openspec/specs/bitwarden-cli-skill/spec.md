## MODIFIED Requirements

### Requirement: Hermes seeds a repo-managed Bitwarden skill
The default Hermes skill inventory SHALL include a repo-managed Bitwarden skill that is copied into `~/.hermes/skills` on first start without overwriting an existing user-managed skill directory of the same name.

#### Scenario: Fresh Hermes profile receives the Bitwarden skill
- **WHEN** a fresh Hermes profile receives the default seeded skill tree
- **THEN** the seeded skills include the repo-managed Bitwarden skill
- **AND** the skill content describes the supported Bitwarden Password Manager CLI workflow

#### Scenario: Existing Bitwarden skill is preserved
- **WHEN** a Bitwarden skill directory already exists in `~/.hermes/skills`
- **THEN** runtime skill seeding leaves the existing directory unchanged

### Requirement: Bitwarden skill defines the official CLI workflow
The repo-managed Bitwarden skill SHALL instruct agents to use the official `bw` Password Manager CLI workflow and the repo-defined persisted CLI state path.

#### Scenario: Skill documents the required runtime state
- **WHEN** maintainers inspect the Bitwarden skill content
- **THEN** the skill names `BITWARDENCLI_APPDATA_DIR=/home/hermes/.local/state/bitwarden-cli`
- **AND** the skill explains the repo-defined Hermes-managed `bw` configuration/state path
- **AND** the skill names `/run/user/3000/ghostship-bitwarden/session.env` as the runtime session file

#### Scenario: Skill documents Password Manager CLI auth
- **WHEN** maintainers inspect the Bitwarden skill content
- **THEN** the skill directs agents to use `bw-unlock` and `bw-lock` for session management before official `bw` sync and item retrieval commands
- **AND** the skill avoids the retired Secrets Manager access-token workflow as supported guidance

### Requirement: Bitwarden skill covers shared secret retrieval conventions
The repo-managed Bitwarden skill SHALL describe how agents use Bitwarden as the source of truth for service credentials and automation-compatible website credentials, SHALL distinguish those secrets from local topology values that remain in env/config, and SHALL prefer narrow per-command secret materialization over a broad shared shell environment.

#### Scenario: Skill covers machine-account secret usage
- **WHEN** maintainers inspect the Bitwarden skill content
- **THEN** the skill explains that the agent should use an operator-managed Bitwarden vault workflow
- **AND** the skill describes project-scoped secrets as the supported sharing model for service credentials and compatible website credentials

#### Scenario: Skill covers local-config versus secret boundaries
- **WHEN** maintainers inspect the Bitwarden skill content
- **THEN** the skill describes service URLs, hostnames, ports, profile names, and paths as local env/config values by default
- **AND** the skill describes passwords, tokens, API keys, and similar credentials as Bitwarden-managed secrets

#### Scenario: Skill covers JSON-friendly per-command secret retrieval
- **WHEN** maintainers inspect the Bitwarden skill content
- **THEN** the skill directs agents to use `bw` retrieval commands that return structured secret data suitable for downstream scripting
- **AND** the skill describes exporting or injecting only the secret values needed for a specific downstream command
- **AND** the skill describes changedetection credentials as a concrete service-secret workflow
