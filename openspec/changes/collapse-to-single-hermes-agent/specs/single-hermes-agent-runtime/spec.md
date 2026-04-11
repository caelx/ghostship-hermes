## ADDED Requirements

### Requirement: The image SHALL expose one authoritative managed Hermes agent surface
The Hermes image SHALL treat `/home/hermes/.hermes` as the single authoritative managed Hermes agent surface and SHALL NOT require repo-owned named profiles for normal runtime operation.

#### Scenario: Managed boot materializes one runtime surface
- **WHEN** the image boots and managed bootstrap prepares persisted `/home/hermes`
- **THEN** the authoritative managed Hermes config, env, auth, skills, `SOUL.md`, and gateway state live under `/home/hermes/.hermes`
- **AND** the runtime does not require operators to select or inspect a repo-owned named profile for the supported default workflow

#### Scenario: Repo-owned named profiles are removed from the supported contract
- **WHEN** maintainers inspect the image module, validation, or docs after this change
- **THEN** the supported runtime contract does not describe `assistant`, `operations`, `supervisor`, or another repo-owned profile fleet as the primary operating surface
- **AND** repo-owned workflows do not depend on `hermes -p <profile>` for the default managed agent path

### Requirement: The image SHALL converge one canonical managed state layout
The Hermes image SHALL converge one canonical set of managed runtime paths for config, auth, env, skills, `SOUL.md`, and liveness markers under the root managed Hermes home.

#### Scenario: Canonical managed paths are stable across restart and replacement
- **WHEN** the container restarts or is replaced while `/home/hermes` persists
- **THEN** the managed config remains rooted at `/home/hermes/.hermes/config.yaml`
- **AND** the managed env remains rooted at `/home/hermes/.hermes/.env`
- **AND** the managed auth remains rooted at `/home/hermes/.hermes/auth.json`
- **AND** the managed skills and `SOUL.md` remain rooted under `/home/hermes/.hermes`
- **AND** the managed gateway liveness marker remains rooted at `/home/hermes/.hermes/gateway.pid`

### Requirement: Repository documentation SHALL describe only the single-agent topology
The repository documentation SHALL describe one managed Hermes agent topology and SHALL remove instructions that treat named profiles as the supported runtime contract.

#### Scenario: Core docs are rewritten for the single-agent runtime
- **WHEN** an operator or maintainer reads the repo documentation after this change
- **THEN** the docs describe one managed agent, one managed env file, one managed skill tree, one `SOUL.md`, and one managed gateway service
- **AND** the docs do not continue presenting removed profile-scoped paths, services, or workflows as supported behavior
