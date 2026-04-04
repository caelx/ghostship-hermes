## MODIFIED Requirements

### Requirement: Workstation persistence uses `/home/hermes`, `/workspace`, and `/nix`
The workstation SHALL treat `/home/hermes` as the canonical persisted home and Hermes state volume, `/workspace` as the persisted work-products volume, and `/nix` as persisted Nix package/build state when a reusable persistent `/nix` mount is provided.

#### Scenario: Runtime contract defines the rebuilt persisted roots
- **WHEN** maintainers inspect the rebuilt runtime docs and container contract
- **THEN** the docs identify `/home/hermes` as the persisted home and Hermes state root
- **AND** the docs identify `/workspace` as the persisted work-products root
- **AND** the docs describe persisted `/nix` support for user-level Nix installs and build outputs

#### Scenario: Reused persisted roots restore runtime state
- **WHEN** a new container starts with the same `/home/hermes`, `/workspace`, and reusable `/nix` mounts
- **THEN** the workstation sees the previously persisted Hermes state, profiles, work products, and Nix-managed state from those mounts

### Requirement: Boot preparation never overwrites existing persisted volume data
Boot-time preparation SHALL create missing runtime directories and repair ownership, but SHALL NOT overwrite existing data already present in `/home/hermes`, `/workspace`, or persisted `/nix`.

#### Scenario: Missing persisted directory is prepared
- **WHEN** a required runtime directory does not yet exist
- **THEN** boot preparation creates it with the expected ownership and permissions

#### Scenario: Existing persisted file wins
- **WHEN** persisted content already exists
- **THEN** boot preparation leaves that content intact

## ADDED Requirements

### Requirement: Whole-home persistence preserves later-installed coding-agent state
Persisting the whole `/home/hermes` tree SHALL preserve later-installed coding-agent config, state, caches, and tool-managed directories without a curated top-level symlink list.

#### Scenario: XDG-backed tool state survives replacement
- **WHEN** later-installed tools write under `~/.config`, `~/.local`, or `~/.cache`
- **AND** the container is replaced while reusing `/home/hermes`
- **THEN** that state remains present after replacement

#### Scenario: Agent-specific home directories survive replacement
- **WHEN** later-installed tools create directories such as `~/.agents`, `~/.agent-browser`, `~/.codex`, `~/.gemini`, `~/.copilot`, `~/.npm`, `~/.bun`, `~/.ssh`, `~/.gnupg`, or `~/.pki`
- **AND** the container is replaced while reusing `/home/hermes`
- **THEN** those directories and their contents remain present after replacement

#### Scenario: Later-installed opencode state survives replacement
- **WHEN** the runtime user installs `opencode`, runs it long enough to create config or state under its active XDG-backed paths, and the container is later replaced while reusing `/home/hermes` and `/nix`
- **THEN** the resulting `opencode` config/state remains present after replacement

### Requirement: Persisted `/nix` SHALL preserve user-level Nix profile installs across container replacement
When the runtime is started with a reusable persisted `/nix` mount, user-level Nix profile installs SHALL remain available after container replacement.

#### Scenario: User-level Nix install survives replacement
- **WHEN** the runtime user installs a package with `nix profile install` and the container is later replaced while reusing the same `/nix` mount
- **THEN** the installed package remains available to the runtime user in the new container
- **AND** the rebuilt runtime docs describe `/nix` persistence as required for this behavior
