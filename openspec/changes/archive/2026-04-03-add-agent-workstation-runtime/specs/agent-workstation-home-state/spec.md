## ADDED Requirements

### Requirement: Workstation persistence is split across `/opt/data`, `/workspace`, and `/nix`
The agent workstation SHALL treat `/opt/data` as the canonical persisted Hermes state volume, `/workspace` as the persisted work-products volume, and `/nix` as persisted package/build state when a safe persistent `/nix` mount is provided.

#### Scenario: Runtime contract defines the persisted roots
- **WHEN** maintainers inspect the runtime docs and container contract
- **THEN** the docs identify `/opt/data` as the canonical Hermes state root
- **AND** the docs identify `/workspace` as the persisted work-products root
- **AND** the docs describe persisted `/nix` support for Nix-installed tools and build outputs

#### Scenario: Reused persisted roots restore workstation state
- **WHEN** a new container starts with the same `/opt/data`, `/workspace`, and safe `/nix` mounts
- **THEN** the workstation sees the previously persisted Hermes state, work products, and Nix-managed state from those mounts

### Requirement: `/opt/data/home` backs the persisted home facade
The workstation SHALL keep a persisted home facade under `/opt/data/home` and expose selected home directories through symlinks in `/home/hermes`.

#### Scenario: Managed home paths resolve into `/opt/data/home`
- **WHEN** the workstation prepares `/home/hermes`
- **THEN** the managed home directories are symlinks into `/opt/data/home`
- **AND** those symlinks make HOME-anchored state persistent across rebuilds and restarts

### Requirement: Boot migration never overwrites existing persisted volume data
Boot-time migration SHALL copy image/runtime defaults into the persisted destinations only when the destination path is missing, and SHALL NOT overwrite existing data already present in `/opt/data`, `/workspace`, or persisted `/nix`.

#### Scenario: Missing persisted file is seeded
- **WHEN** a managed persisted destination does not yet exist
- **THEN** boot migration copies the default file or directory into the persisted location

#### Scenario: Existing persisted file wins
- **WHEN** the persisted destination already exists
- **THEN** boot migration leaves the persisted content intact
- **AND** the runtime does not overwrite it with image defaults during boot

### Requirement: Workstation state is single-writer
The workstation SHALL assume one active container instance per persisted `/opt/data` and `/workspace` set so mutable state is not shared concurrently between multiple running containers.

#### Scenario: Docs warn against concurrent use
- **WHEN** maintainers inspect the workstation persistence guidance
- **THEN** the docs warn that one persisted workstation state set should not be shared by multiple running workstation containers at the same time
