## ADDED Requirements

### Requirement: Hermes image SHALL bundle `ghostship-n8n` as a first-class utility
The Hermes image SHALL include a repo-owned `ghostship-n8n` executable on `PATH`, and the package SHALL be exposed through the repo's normal flake outputs and image wiring.

#### Scenario: Image build exposes `ghostship-n8n`
- **WHEN** the Hermes image is built from the repo flake
- **THEN** the resulting runtime includes the `ghostship-n8n` executable on `PATH`
- **AND** the utility is bundled alongside the other repo-owned `ghostship-*` tools

#### Scenario: Repo evaluation covers the n8n package
- **WHEN** maintainers inspect flake packages or run normal repo evaluation
- **THEN** the repo exposes `ghostship-n8n` as a first-class package output
- **AND** the Hermes image package depends on that evaluated package path

### Requirement: `ghostship-n8n` SHALL cover the full official n8n public API in repo-style snake_case commands
`ghostship-n8n` SHALL expose dedicated client methods and CLI commands for every operation in the persisted official n8n public API contract, with names normalized into the same snake_case style used by the other `ghostship-*` service CLIs.

#### Scenario: Every mirrored public API operation has a dedicated wrapper
- **WHEN** maintainers compare the persisted bundled n8n public API snapshot to the client and CLI inventory
- **THEN** every mirrored public API operation has a dedicated typed client method
- **AND** every mirrored public API operation has a dedicated snake_case CLI command

#### Scenario: Generic passthrough remains the fallback only
- **WHEN** maintainers inspect the command inventory for `ghostship-n8n`
- **THEN** the utility includes a generic `request` escape hatch
- **AND** the dedicated command surface still covers the full mirrored public API contract

### Requirement: `ghostship-n8n` SHALL follow the shared Ghostship CLI contract
`ghostship-n8n` SHALL emit JSON by default, accept the shared hard timeout contract, and expose dry-run request rendering for write and delete operations.

#### Scenario: Every command accepts the standard timeout option
- **WHEN** maintainers inspect `ghostship-n8n --help` and subcommand help output
- **THEN** every invocation accepts `--timeout`
- **AND** the default hard timeout is `30` seconds

#### Scenario: Mutations support dry-run request inspection
- **WHEN** maintainers inspect write and delete commands for `ghostship-n8n`
- **THEN** each mutation command accepts `--dry-run`
- **AND** dry-run prints the exact request object instead of calling the API

### Requirement: `ghostship-n8n` SHALL use environment-driven n8n authentication and endpoint configuration
`ghostship-n8n` SHALL authenticate with n8n through environment-provided service configuration, and it SHALL support the documented public API base path and version model for self-hosted deployments.

#### Scenario: Utility reads the documented n8n service environment
- **WHEN** maintainers inspect the CLI docs and client configuration
- **THEN** the utility names `N8N_URL` and `N8N_API_KEY` as the primary service environment variables
- **AND** the utility documents optional public API path or version overrides for non-default self-hosted endpoint settings

#### Scenario: Requests use the upstream API key header and configured public API base
- **WHEN** `ghostship-n8n` calls authenticated n8n public API endpoints
- **THEN** it sends the configured API key using the `X-N8N-API-KEY` request header
- **AND** it constructs request URLs against the configured n8n public API path and version rather than assuming a single hardcoded base path

### Requirement: The repo SHALL persist a stable upstream n8n public API reference
The repo SHALL store a bundled official n8n public API artifact in `docs/api/` and SHALL pair it with a repo-owned Markdown reference sheet for the utility.

#### Scenario: Bundled upstream API snapshot is committed in the repo
- **WHEN** maintainers inspect `docs/api/`
- **THEN** the repo contains a committed bundled n8n public API snapshot
- **AND** the raw artifact filename follows the repo's `*-openapi.json` naming convention

#### Scenario: Markdown reference and coverage index are updated
- **WHEN** maintainers inspect the API docs inventory after this change
- **THEN** `docs/api/n8n.md` documents auth, pagination, endpoint groups, and utility coverage
- **AND** `docs/api/README.md` includes `ghostship-n8n` in the coverage matrix
