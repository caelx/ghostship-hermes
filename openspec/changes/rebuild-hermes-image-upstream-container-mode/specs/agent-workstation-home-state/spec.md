## MODIFIED Requirements

### Requirement: Workstation persistence is split across `/opt/data`, `/workspace`, and `/nix`
The agent workstation SHALL treat `/data` as the canonical persisted Hermes state volume, `/workspace` as the persisted work-products volume, and `/nix` as persisted Nix package/build state when a reusable persistent `/nix` mount is provided.

#### Scenario: Runtime contract defines the rebuilt persisted roots
- **WHEN** maintainers inspect the rebuilt runtime docs and container contract
- **THEN** the docs identify `/data` as the canonical Hermes state root
- **AND** the docs identify `/workspace` as the persisted work-products root
- **AND** the docs describe persisted `/nix` support for user-level Nix installs and build outputs

#### Scenario: Reused persisted roots restore runtime state
- **WHEN** a new container starts with the same `/data`, `/workspace`, and reusable `/nix` mounts
- **THEN** the workstation sees the previously persisted Hermes state, work products, and Nix-managed state from those mounts

### Requirement: `/data/home` backs the persisted home facade
The workstation SHALL keep a persisted home facade under `/data/home` and expose selected home directories through symlinks in `/home/hermes`.

#### Scenario: Managed home paths resolve into `/data/home`
- **WHEN** the rebuilt workstation prepares `/home/hermes`
- **THEN** the managed home directories are symlinks into `/data/home`
- **AND** those symlinks make HOME-anchored state persistent across container replacement and restart

### Requirement: The home facade SHALL NOT absorb `HERMES_HOME`
The persisted home facade under `/data/home` SHALL remain separate from Hermes' canonical state root at `/data/.hermes`.

#### Scenario: Canonical `HERMES_HOME` stays outside the home facade
- **WHEN** maintainers inspect the rebuilt persistence layout
- **THEN** `/data/.hermes` remains the canonical `HERMES_HOME`
- **AND** the runtime does not redefine `HERMES_HOME` to a path under `/data/home`
- **AND** the home-facade persistence logic does not move Hermes state into the general HOME tree

### Requirement: Boot migration never overwrites existing persisted volume data
Boot-time migration SHALL copy runtime defaults into the persisted destinations only when the destination path is missing, and SHALL NOT overwrite existing data already present in `/data`, `/workspace`, or persisted `/nix`.

#### Scenario: Missing persisted file is seeded
- **WHEN** a managed persisted destination does not yet exist
- **THEN** boot migration copies the default file or directory into the persisted location

#### Scenario: Existing persisted file wins
- **WHEN** the persisted destination already exists
- **THEN** boot migration leaves the persisted content intact
- **AND** the runtime does not overwrite it with image defaults during boot

### Requirement: Workstation state is single-writer
The workstation SHALL assume one active container instance per persisted `/data`, `/workspace`, and `/nix` set so mutable state is not shared concurrently between multiple running containers.

#### Scenario: Docs warn against concurrent use
- **WHEN** maintainers inspect the rebuilt persistence guidance
- **THEN** the docs warn that one persisted workstation state set should not be shared by multiple running workstation containers at the same time

## ADDED Requirements

### Requirement: The home facade SHALL persist broad common user-state directories
The rebuilt workstation SHALL persist broad common HOME-backed user-state directories through `/data/home`, including at least `~/.config`, `~/.local`, and `~/.cache`.

#### Scenario: Common XDG directories persist through the facade
- **WHEN** maintainers inspect the rebuilt persisted home layout
- **THEN** `~/.config`, `~/.local`, and `~/.cache` resolve into `/data/home`
- **AND** those directories survive container replacement when `/data` is reused

### Requirement: The home facade SHALL preserve later-installed coding-agent config and state
The rebuilt workstation SHALL preserve the needed top-level HOME-backed directories used by coding-agent tools that are removed from the default image package set but may be installed later by the operator or by Hermes.

#### Scenario: Hermes profile home survives container replacement
- **WHEN** upstream Hermes creates named profiles under `~/.hermes/profiles/...`
- **THEN** `~/.hermes` resolves into persisted HOME-backed storage under `/data/home`
- **AND** those profile directories survive container replacement without changing the canonical `HERMES_HOME=/data/.hermes`

#### Scenario: User-installed coding-agent tools keep XDG-backed state
- **WHEN** coding-agent tools such as Codex, Gemini CLI, Opencode, OpenSpec, or comparable later-installed tools write config or cache data under the user's standard XDG locations
- **THEN** that state resolves into the persisted `/data/home` facade
- **AND** it survives container replacement when `/data` is reused

#### Scenario: Known agent-specific home directories remain persistent
- **WHEN** later-installed coding-agent tools create or use agent-specific directories such as `~/.agent-browser`, `~/.agents`, `~/.codex`, `~/.copilot`, or `~/.gemini`
- **THEN** those directories resolve into persisted HOME-backed storage under `/data/home`
- **AND** their contents survive container replacement when `/data` is reused

#### Scenario: Browser automation config and cache survive container replacement
- **WHEN** browser automation tools write state under paths such as `~/.config/browseruse`, `~/.config/chromium`, `~/.config/google-chrome-for-testing`, `~/.cache/ms-playwright`, or `~/.cache/puppeteer`
- **THEN** that state resolves into the persisted `/data/home` facade
- **AND** it survives container replacement when `/data` is reused

#### Scenario: Agent-browser sessions survive container replacement
- **WHEN** `agent-browser` stores session data under `~/.agent-browser`
- **THEN** that directory resolves into persisted HOME-backed storage under `/data/home`
- **AND** its contents survive container replacement when `/data` is reused

#### Scenario: Later-installed opencode state survives container replacement
- **WHEN** the runtime user installs `opencode`, runs it long enough to create its config or state under its active XDG-backed paths such as `~/.config/opencode`, `~/.local/share/opencode`, `~/.local/state/opencode`, and `~/.cache/opencode`, and the container is later replaced while reusing `/data` and `/nix`
- **THEN** the resulting `opencode` config/state remains present after replacement
- **AND** the rebuilt validation flow proves that the persisted home contract preserves that state without `opencode` being preinstalled in the base image

#### Scenario: Existing `.agents` content survives container replacement
- **WHEN** the runtime home contains agent instructions or skills under `~/.agents` and the container is later replaced while reusing `/data`
- **THEN** the `~/.agents` tree remains present after replacement
- **AND** the home facade does not discard or relocate that persisted content

#### Scenario: Toolchain and credential roots remain persistent when present
- **WHEN** the runtime home contains needed top-level user-managed toolchain or credential roots such as `~/.npm`, `~/.bun`, `~/.ssh`, `~/.gnupg`, or `~/.pki`
- **THEN** those directories remain in persisted HOME-backed storage under `/data/home`
- **AND** the rebuilt home-facade contract preserves them across container replacement when `/data` is reused

#### Scenario: Persisted tool roots remain updateable
- **WHEN** a later-installed tool keeps code or dependencies under persisted HOME-backed storage and the operator or Hermes updates that tool through its supported install path
- **THEN** the updated code remains present after restart or container replacement
- **AND** the runtime does not restore an older image-seeded copy over the updated persisted tool root on boot

### Requirement: Persisted `/nix` SHALL preserve user-level Nix profile installs across container replacement
When the runtime is started with a reusable persisted `/nix` mount, user-level Nix profile installs SHALL remain available after container replacement.

#### Scenario: Runtime prepares the Nix daemon socket path
- **WHEN** the rebuilt runtime prepares persisted `/nix`
- **THEN** it creates a writable `/nix/var/nix/daemon-socket`
- **AND** the image starts `nix-daemon.socket` only after that persisted path exists

#### Scenario: User-level Nix install survives replacement
- **WHEN** the runtime user installs a package with `nix profile install` and the container is later replaced while reusing the same `/nix` mount
- **THEN** the installed package remains available to the runtime user in the new container
- **AND** the rebuilt runtime docs describe `/nix` persistence as required for this behavior
