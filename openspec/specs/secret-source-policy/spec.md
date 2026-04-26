## ADDED Requirements

### Requirement: Repo classifies bootstrap inputs, secrets, and local topology separately
The repo SHALL define a distinct policy for bootstrap secret inputs, Bitwarden-managed secrets, and local environment/config values so operators and maintainers can tell which values belong in each system.

#### Scenario: Bootstrap secret is defined separately from service credentials
- **WHEN** maintainers inspect the repo policy docs
- **THEN** the policy identifies `BITWARDENCLI_APPDATA_DIR` as the persisted Bitwarden CLI state path
- **AND** the policy identifies Bitwarden authentication state as operator-managed local state rather than a service credential

#### Scenario: Local topology stays outside Bitwarden by default
- **WHEN** maintainers inspect the repo policy docs
- **THEN** the policy defines service URLs, hostnames, ports, profile names, and workspace-specific paths as local environment/config values by default
- **AND** the policy does not describe those values as Bitwarden-managed secrets unless they contain credential material

### Requirement: Bitwarden is the source of truth for machine-manageable credentials
The repo SHALL treat Bitwarden as the source of truth for service credentials and website automation credentials that fit an operator-managed vault workflow.

#### Scenario: Service credentials are sourced from Bitwarden
- **WHEN** maintainers inspect the repo policy docs
- **THEN** the policy describes service API keys, bearer tokens, usernames, passwords, cookie seeds, and similar credentials as Bitwarden-managed secrets
- **AND** the policy allows those secrets to be materialized into environment variables only as a runtime interface for the command that needs them

#### Scenario: Website credential support has an explicit boundary
- **WHEN** maintainers inspect the repo policy docs
- **THEN** the policy includes website automation credentials that can be represented as normal machine secrets
- **AND** the policy excludes interactive-only authentication models such as passkeys, WebAuthn hardware prompts, and human SSO sessions from the default Bitwarden workflow

### Requirement: Repo documentation aligns on runtime environment variable usage
The repo SHALL document environment variables for `ghostship-*` utilities as a runtime consumption interface and SHALL not present them as the preferred durable source of truth for secrets.

#### Scenario: Docs describe env vars as the runtime interface
- **WHEN** maintainers inspect the central repo documentation
- **THEN** the docs explain that `ghostship-*` utilities may still consume environment variables at process launch time
- **AND** the docs distinguish that runtime interface from the durable storage of service credentials in Bitwarden

#### Scenario: Docs discourage broad ambient secret environments
- **WHEN** maintainers inspect the central repo documentation
- **THEN** the docs prefer materializing only the secret values needed for a specific command or workflow
- **AND** the docs do not recommend exporting a long-lived global shell environment containing every service secret by default
