## ADDED Requirements

### Requirement: Hermes image SHALL bundle `ghostship-changedetection` as a first-class utility
The Hermes image SHALL include a repo-owned `ghostship-changedetection` executable on `PATH`, and the package SHALL be exposed through the repo's normal flake outputs and image wiring.

#### Scenario: Image build exposes `ghostship-changedetection`
- **WHEN** the Hermes image is built from the repo flake
- **THEN** the resulting runtime includes the `ghostship-changedetection` executable on `PATH`
- **AND** the utility is bundled alongside the other repo-owned `ghostship-*` tools

#### Scenario: Repo evaluation covers the changedetection package
- **WHEN** maintainers inspect flake packages or run normal flake evaluation
- **THEN** the repo exposes `ghostship-changedetection` as a first-class package output
- **AND** the Hermes image package depends on that evaluated package path

### Requirement: `ghostship-changedetection` SHALL cover the full stable upstream API in repo-style snake_case commands
`ghostship-changedetection` SHALL expose dedicated client methods and CLI commands for every operation in the persisted stable upstream `changedetection.io` API contract, with names normalized into the same snake_case style used by the other `ghostship-*` service CLIs.

#### Scenario: Every stable upstream operation has a dedicated wrapper
- **WHEN** maintainers compare the persisted upstream `changedetection.io` API snapshot to the client and CLI inventory
- **THEN** every stable upstream operation has a dedicated typed client method
- **AND** every stable upstream operation has a dedicated snake_case CLI command

#### Scenario: Generic passthrough remains the fallback only
- **WHEN** maintainers inspect the command inventory for `ghostship-changedetection`
- **THEN** the utility includes a generic `request` escape hatch
- **AND** the dedicated command surface still covers the full stable upstream API contract

### Requirement: `ghostship-changedetection` SHALL follow the shared Ghostship CLI contract
`ghostship-changedetection` SHALL emit JSON by default, accept the shared hard timeout contract, and expose dry-run request rendering for write and delete operations.

#### Scenario: Every command accepts the standard timeout option
- **WHEN** maintainers inspect `ghostship-changedetection --help` and subcommand help output
- **THEN** every invocation accepts `--timeout`
- **AND** the default hard timeout is `30` seconds

#### Scenario: Mutations support dry-run request inspection
- **WHEN** maintainers inspect write and delete commands for `ghostship-changedetection`
- **THEN** each mutation command accepts `--dry-run`
- **AND** dry-run prints the exact request object instead of calling the remote service

### Requirement: `ghostship-changedetection` SHALL use environment-driven changedetection authentication
`ghostship-changedetection` SHALL authenticate to `changedetection.io` with environment-provided service configuration so Hermes can retrieve and inject credentials without interactive prompts.

#### Scenario: Utility reads the documented service environment
- **WHEN** maintainers inspect the CLI docs and client configuration
- **THEN** the utility names `CHANGEDETECTION_URL` and `CHANGEDETECTION_API_KEY` as the required service environment variables
- **AND** the documented auth flow requires no interactive login

#### Scenario: Requests include the upstream API key header
- **WHEN** `ghostship-changedetection` calls authenticated `changedetection.io` endpoints
- **THEN** it sends the configured API key using the upstream-supported request header
- **AND** read and write operations use the same environment-driven auth model

### Requirement: The repo SHALL persist a stable upstream changedetection API reference
The repo SHALL store a stable upstream `changedetection.io` machine-readable API artifact in `docs/api/` and SHALL pair it with a repo-owned Markdown reference sheet for the utility.

#### Scenario: Raw upstream API snapshot is committed in the repo
- **WHEN** maintainers inspect `docs/api/`
- **THEN** the repo contains a persisted stable upstream `changedetection.io` OpenAPI snapshot
- **AND** the raw artifact filename follows the repo's `*-openapi.json` naming convention

#### Scenario: Markdown reference and coverage index are updated
- **WHEN** maintainers inspect the API docs inventory after this change
- **THEN** `docs/api/changedetection.md` documents auth, endpoint groups, and utility coverage
- **AND** `docs/api/README.md` includes `ghostship-changedetection` in the coverage matrix
