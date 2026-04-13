## MODIFIED Requirements

### Requirement: Runtime validation executes supported CLI entrypoints
The workstation SHALL validate supported runtime CLI execution with command-level smoke tests when command discovery alone is insufficient to prove the runtime path works.

#### Scenario: Agent-browser validation executes the command
- **WHEN** maintainers run the Hermes image validation suite for a build that advertises `agent-browser` on the supported runtime path
- **THEN** the suite executes `agent-browser --help` or an equivalent non-destructive smoke command
- **AND** the suite does not treat a passing `command -v agent-browser` check by itself as sufficient proof that the supported browser command works

#### Scenario: Gemini validation executes the command
- **WHEN** maintainers run the Hermes image validation suite for a build that advertises `gemini` on the supported runtime path
- **THEN** the suite executes `gemini --help` or an equivalent non-destructive smoke command from the Hermes-user default PATH
- **AND** the suite does not treat a passing `command -v gemini` check by itself as sufficient proof that the supported Gemini CLI path works

## ADDED Requirements

### Requirement: Managed tooling refresh installs the approved npm agent CLI set
The workstation SHALL converge the approved npm-managed agent CLI set into the persisted tooling project under `/home/hermes` so supported fast-moving CLIs remain available across boot, timer refresh, and image replacement.

#### Scenario: Boot and timer refresh install the approved npm CLI set
- **WHEN** the managed user-tooling refresh converges the Hermes runtime tooling project
- **THEN** the persisted npm-managed CLI set includes `@openai/codex`, `@google/gemini-cli`, and `opencode-ai`
- **AND** the projected Hermes-user PATH exposes `codex`, `gemini`, and `opencode` from `/home/hermes/.local/bin`
- **AND** supported exceptions such as `agent-browser` may remain outside that npm-managed set when the image declares them as image-managed commands
