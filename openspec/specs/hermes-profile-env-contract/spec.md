## MODIFIED Requirements

### Requirement: Managed agent `.env` is the operator-facing source of truth for runtime env
The workstation SHALL treat `/home/hermes/.hermes/.env` as an optional downstream-owned persisted env file rather than as a repo-generated artifact, and the image SHALL NOT regenerate that file on boot.

#### Scenario: Operator-owned `.env` is left intact across restart
- **WHEN** `/home/hermes/.hermes/.env` already exists in the persisted home volume
- **THEN** workstation startup leaves that file intact
- **AND** the runtime does not rewrite it from a repo-owned allowlist projection

#### Scenario: Missing `.env` does not require repo-owned file generation
- **WHEN** `/home/hermes/.hermes/.env` is absent at startup
- **THEN** the runtime may start from downstream-provided container environment without generating a replacement `.env`
- **AND** the supported contract does not require boot-time synthesis of that file

### Requirement: Managed `.env` changes remain visible to service restart wiring
The workstation SHALL keep operator-facing runtime env changes visible through the normal downstream env surfaces used by the running services, without depending on a repo-owned bootstrap rewrite step.

#### Scenario: Service runtime sees downstream-owned env changes
- **WHEN** the operator updates supported runtime env through the documented downstream mechanism
- **THEN** the affected services read the updated values from that downstream-owned mechanism
- **AND** the runtime does not require a repo-owned `.env` regeneration step to make the change effective

## REMOVED Requirements

### Requirement: Bootstrap projects the supported runtime env inventory into the managed `.env`
**Reason**: The new workstation image moves operator-facing env ownership to downstream deployment config or downstream-owned persisted files instead of repo-owned bootstrap projection.
**Migration**: Downstream deployments SHALL supply supported runtime env through Compose, `docker run`, env files, or an operator-managed `/home/hermes/.hermes/.env` in the persisted home volume.

### Requirement: Bootstrap projects generic Discord configuration into the managed `.env`
**Reason**: Discord env remains supported, but the image no longer owns a special projection step for writing those values into managed home state.
**Migration**: Downstream deployments SHALL supply the supported Discord env directly through the documented downstream env mechanism.

### Requirement: Bootstrap projects managed webhook listener env into the managed `.env`
**Reason**: Webhook env remains part of the supported operator-facing env surface, but it is no longer copied into a repo-generated `.env` file.
**Migration**: Downstream deployments SHALL supply webhook env directly and persist operator-managed `.env` only if they want file-backed config in home state.

### Requirement: Bootstrap maps the deployment webhook secret source into Hermes-facing env
**Reason**: The new contract removes repo-owned env translation during boot.
**Migration**: Downstream deployments SHALL pass the Hermes-facing webhook env names directly through the documented operator env contract.

### Requirement: Managed bootstrap rewrites the managed `.env` idempotently
**Reason**: The workstation no longer supports a repo-owned `.env` rewrite loop.
**Migration**: Operators SHALL manage `.env` content directly if they want a persisted file under `/home/hermes/.hermes`.

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
- **AND** the docs identify `DISCORD_HOME_CHANNEL` as required downstream env when the Discord gateway is enabled
- **AND** the docs identify `GHOSTSHIP_ROUTER_CHANNEL` as the only downstream-owned Discord channel pin env in the supported contract
- **AND** the docs identify `GHOSTSHIP_CODEX_CHANNEL` as removed from the supported downstream env contract
- **AND** the docs explain that Codex auth remains persisted home state rather than a downstream env key
