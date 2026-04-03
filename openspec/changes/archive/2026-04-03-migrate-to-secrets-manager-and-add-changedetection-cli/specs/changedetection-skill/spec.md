## ADDED Requirements

### Requirement: Hermes SHALL seed a repo-managed changedetection skill
The default Hermes skill inventory SHALL include a repo-managed `changedetection` skill that is copied into `~/.hermes/skills` on first start without overwriting an existing user-managed skill directory of the same name.

#### Scenario: Fresh Hermes profile receives the changedetection skill
- **WHEN** a fresh Hermes profile receives the default seeded skill tree
- **THEN** the seeded skills include the repo-managed `changedetection` skill
- **AND** the skill is available alongside the other repo-managed service skills

#### Scenario: Existing changedetection skill is preserved
- **WHEN** a `changedetection` skill directory already exists in `~/.hermes/skills`
- **THEN** runtime skill seeding leaves the existing directory unchanged

### Requirement: The changedetection skill SHALL teach the `bws` to `ghostship-changedetection` workflow
The repo-managed `changedetection` skill SHALL instruct agents to retrieve `changedetection.io` credentials through Bitwarden Secrets Manager and then operate the service with `ghostship-changedetection`.

#### Scenario: Skill names the secret retrieval prerequisites
- **WHEN** maintainers inspect the changedetection skill content
- **THEN** the skill identifies Bitwarden Secrets Manager as the supported credential source
- **AND** the skill names `CHANGEDETECTION_URL` and `CHANGEDETECTION_API_KEY` as the service configuration values Hermes needs before using the CLI

#### Scenario: Skill directs agents to use the dedicated CLI surface
- **WHEN** maintainers inspect the changedetection skill content
- **THEN** the skill tells agents to prefer dedicated `ghostship-changedetection` commands over generic passthrough calls
- **AND** the skill treats the persisted repo API docs as the canonical reference for the service contract

### Requirement: The changedetection skill SHALL follow inspect -> dry-run -> mutate -> verify workflows
The repo-managed `changedetection` skill SHALL describe changedetection automation as an inspect-first workflow with guarded mutations and explicit verification.

#### Scenario: Skill covers safe mutation sequencing
- **WHEN** maintainers inspect the changedetection skill content
- **THEN** the skill directs agents to inspect current service state before mutating it
- **AND** the skill directs agents to use `--dry-run` on write and delete commands before the real mutation

#### Scenario: Skill covers post-mutation verification
- **WHEN** maintainers inspect the changedetection skill content
- **THEN** the skill directs agents to verify resulting state with dedicated read commands after changes
- **AND** the workflow guidance stays short, trigger-rich, and service-oriented rather than duplicating the full API reference
