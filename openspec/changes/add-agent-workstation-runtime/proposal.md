## Why

The current workstation change is centered on persisting `/home/hermes`, but upstream Hermes Docker semantics center on `HERMES_HOME=/opt/data`. Real Docker probes showed that default Hermes state persists in `/opt/data`, while named profiles, wrappers, and `~/.config` state do not, so the sprint needs to be rewritten around a Hermes-native persistence model that preserves both Hermes state and the wider agent workstation.

## What Changes

- **BREAKING** Make `/opt/data` the canonical persisted Hermes volume and keep `HERMES_HOME=/opt/data` so the container matches upstream Hermes expectations.
- **BREAKING** Replace the current “persist all of `/home/hermes`” contract with a split model: `/opt/data` for Hermes and persisted home state, `/workspace` for repos and work products, and persisted `/nix` support for Nix-installed tools and build outputs.
- Add a persisted home facade rooted at `/opt/data/home`, with boot-time symlink repair from `/home/hermes` into that tree for `.hermes`, `.config`, `.local`, `.cache`, `.agents`, and related workstation directories.
- Add non-destructive boot migration rules: copy files from image/runtime defaults only when the persisted destination is missing, never overwrite existing volume data, and only replace live home directories with symlinks after migration.
- Keep `systemd`, the custom Ghostship Hermes dashboard stack, Hermes-native profile behavior, and Hermes-native `gateway install` behavior, but make their HOME-anchored state persist through the symlinked home facade.
- Add a separate persisted `/workspace` mount for projects, build artifacts, downloads, and work items, exposed inside the user home as a normal workspace path.
- Support persisted `/nix` so Hermes and the agent can install and run additional software with Nix across container rebuilds and restarts, while documenting the safe mount strategy for Nix-built images.
- Rewrite docs and validation around the new contract, including local Docker tests that prove reused `/opt/data`, `/workspace`, and `/nix` preserve the intended state.

## Capabilities

### New Capabilities
- `agent-workstation-home-state`: Define the canonical persistence layout across `/opt/data`, `/workspace`, and `/nix`, including the `/opt/data/home` facade and non-destructive boot migration rules.
- `agent-workstation-runtime`: Run the workstation with `systemd` while keeping Hermes-native expectations intact, including `HERMES_HOME=/opt/data`, HOME-anchored profile behavior, and persistent user services.
- `agent-workstation-seeding`: Seed repo-managed workstation defaults into the persisted `/opt/data` and `/opt/data/home` trees without overwriting existing persisted state.
- `agent-workstation-updates`: Keep apps and mutable agent assets current through boot-time and timer-driven updates rooted in the persisted workstation layout.

### Modified Capabilities

## Impact

- Container runtime contract, environment variables, and volume layout in `packages/hermes-image/`
- Boot-time directory creation, symlink repair, and migration logic for `/home/hermes`, `/opt/data`, `/workspace`, and `/nix`
- Hermes profile persistence, `gateway install`, user `systemd` services, and wrapper path behavior
- Placement of seeded skills, config, updater state, and managed app installs
- Docker docs, README guidance, changelog entries, and runtime guidance skills
- Local Docker validation flows for rebuild/restart continuity under the new persistence model
