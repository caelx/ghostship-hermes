## MODIFIED Requirements

### Requirement: Workstation persistence is split across `/home/hermes`, `/workspace`, and `/nix`
The workstation SHALL treat `/home/hermes` as the canonical persisted home and Hermes state root, `/workspace` as the persisted work-products root, and `/nix` as the persisted Nix store/profile root when the deployment wants user-installed Nix software to survive container replacement.

#### Scenario: Runtime contract defines the persisted roots
- **WHEN** maintainers inspect the runtime docs and container contract
- **THEN** the docs identify `/home/hermes` as the canonical persisted home and Hermes state root
- **AND** the docs identify `/workspace` as the persisted work-products root
- **AND** the docs identify `/nix` as the persisted Nix store/profile root when downstream wants Nix-managed software to survive container replacement

#### Scenario: Reused persisted roots restore workstation state
- **WHEN** a new container starts with the same `/home/hermes`, `/workspace`, and persisted `/nix` mounts
- **THEN** the workstation sees the previously persisted Hermes state, home-directory state, work products, and Nix-managed state from those mounts

### Requirement: `/home/hermes` is the canonical persisted home
The workstation SHALL keep `HOME=/home/hermes` directly and SHALL store `HERMES_HOME` under that persisted home tree rather than exposing a separate persisted-home facade through `/opt/data` or equivalent indirection.

#### Scenario: Home and Hermes state resolve directly inside the persisted home tree
- **WHEN** the workstation prepares the runtime environment
- **THEN** `HOME` resolves to `/home/hermes`
- **AND** `HERMES_HOME` resolves to `/home/hermes/.hermes`
- **AND** the supported persisted runtime contract does not depend on a `/opt/data/home` facade or equivalent symlink layer

### Requirement: Boot migration never overwrites existing persisted volume data
Boot-time migration or initialization SHALL copy image/runtime defaults into the persisted destinations only when the destination path is missing, and SHALL NOT overwrite existing data already present in `/home/hermes`, `/workspace`, or persisted `/nix`.

#### Scenario: Missing persisted file is seeded
- **WHEN** a managed persisted destination does not yet exist
- **THEN** boot initialization copies the default file or directory into the persisted location

#### Scenario: Existing persisted file wins
- **WHEN** the persisted destination already exists
- **THEN** boot initialization leaves the persisted content intact
- **AND** the runtime does not overwrite it with image defaults during boot

### Requirement: Workstation state is single-writer
The workstation SHALL assume one active container instance per persisted `/home/hermes` and `/workspace` set so mutable state is not shared concurrently between multiple running containers.

#### Scenario: Docs warn against concurrent use
- **WHEN** maintainers inspect the workstation persistence guidance
- **THEN** the docs warn that one persisted workstation state set should not be shared by multiple running workstation containers at the same time

## ADDED Requirements

### Requirement: Downstream docs define the safe `/nix` persistence flow
The workstation docs SHALL describe a supported downstream procedure for first-use seeding and later reuse of `/nix` so operators can preserve the Nix store across restart and container replacement without hiding the image’s required store contents behind an unsafe empty mount.

#### Scenario: Named-volume guidance explains first use and reuse
- **WHEN** a downstream operator follows the documented named-volume pattern for `/nix`
- **THEN** the docs show how the volume is seeded on first use
- **AND** the docs show how the same `/nix` volume is reused across later image upgrades and container replacements

#### Scenario: Bind-mount guidance explains explicit seeding
- **WHEN** a downstream operator chooses a bind-mounted host path for `/nix`
- **THEN** the docs show the explicit one-time seeding step required before normal workstation use
- **AND** the docs warn that an unseeded empty bind mount is not a supported `/nix` startup path
