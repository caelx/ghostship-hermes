## Context

The previous workstation draft made `/home/hermes` the durable root and treated Hermes as one component inside that home-first environment. Live Docker testing against upstream `nousresearch/hermes-agent:latest` showed that Hermes itself expects a different contract: `HERMES_HOME=/opt/data`, with the entrypoint seeding default Hermes files directly into `/opt/data`. The same probe also showed that the official image does not create a symlink from home into `/opt/data`.

That difference matters because Hermes still has HOME-anchored behavior. Named profiles are created under `Path.home() / ".hermes" / "profiles"`, wrapper commands are written into `~/.local/bin`, and user `systemd` units live in `~/.config/systemd/user`. In the upstream image, persisting only `/opt/data` preserves the default Hermes state but loses named profiles, wrappers, and user config on container replacement.

The workstation needs to satisfy both sides at once:
- Hermes must keep its upstream default of `HERMES_HOME=/opt/data`
- the broader agent environment must persist HOME-anchored state and work products
- boot must be non-destructive and must not overwrite the persisted volume contents
- the agent must be able to install software with Nix and keep that state across rebuilds and restarts

The design therefore needs a split persistence model: `/opt/data` for Hermes-native durable state plus a persisted home facade, `/workspace` for projects and artifacts, and `/nix` for Nix-installed tools and build outputs.

## Goals / Non-Goals

**Goals:**
- Keep `HERMES_HOME=/opt/data` so the container matches upstream Hermes Docker behavior.
- Use `/opt/data/home` as the persisted HOME facade and symlink selected home directories into `/home/hermes` at boot.
- Persist HOME-anchored Hermes behavior such as named profiles, wrappers, and user `systemd` units without overwriting existing volume data.
- Add a separate persisted `/workspace` mount for repos, artifacts, downloads, and work items.
- Support persisted `/nix` so Nix-managed installs and build outputs remain available across rebuilds and restarts.
- Keep `systemd` as the runtime model and continue supporting Hermes-native `gateway install` behavior.
- Seed defaults and refresh mutable assets non-destructively, with persisted state always winning over image defaults.
- Validate the persistence theory with real Docker tests using reused `/opt/data`, `/workspace`, and `/nix`.

**Non-Goals:**
- Changing Hermes upstream to remove its split between `HERMES_HOME` and HOME-anchored profile behavior.
- Making `/opt/data` itself look exactly like `~/.hermes` on disk.
- Overwriting persisted user state during boot just because the image has newer defaults.
- Using `sudo` inside the container as part of runtime or bootstrap behavior.
- Treating `/workspace` as part of Hermes control-plane state.

## Decisions

### Keep `HERMES_HOME=/opt/data` and `HOME=/home/hermes`

The runtime should keep upstream Hermes semantics unchanged by setting `HERMES_HOME=/opt/data` while also giving the workstation a normal user home at `/home/hermes`.

Alternative considered: set `HERMES_HOME=/opt/data/home/.hermes`. Rejected because it diverges from upstream Docker semantics and makes the container less Hermes-native at the exact point where `hermes install`, `hermes profile`, and `hermes gateway install` need to behave predictably.

### Add a persisted home facade under `/opt/data/home`

The runtime should create a dedicated persisted home subtree under `/opt/data/home` and repair symlinks into `/home/hermes` for selected directories:

```text
/home/hermes/.hermes   -> /opt/data/home/.hermes
/home/hermes/.config   -> /opt/data/home/.config
/home/hermes/.local    -> /opt/data/home/.local
/home/hermes/.cache    -> /opt/data/home/.cache
/home/hermes/.agents   -> /opt/data/home/.agents
/home/hermes/.codex    -> /opt/data/home/.codex
/home/hermes/.gemini   -> /opt/data/home/.gemini
/home/hermes/.opencode -> /opt/data/home/.opencode
/home/hermes/workspace -> /workspace
```

This keeps `/opt/data` itself reserved for Hermes-native default state while still making HOME-anchored workstation state persistent.

Alternative considered: symlink `/home/hermes/.hermes` directly to `/opt/data`. Rejected because it conflates the upstream Hermes root with the added HOME facade and makes `/opt/data` do two different jobs at once.

### Use non-destructive boot migration and symlink repair

Boot should never treat image defaults as authoritative over persisted state. The migration algorithm should:

1. ensure the destination under `/opt/data/home/...` exists
2. if the live path is already the expected symlink, leave it alone
3. if the live path is a real directory or file, copy only missing entries into the persisted destination
4. replace the live path with the symlink only after the copy-missing step succeeds
5. if both sides already contain conflicting data, preserve the persisted destination and surface the conflict rather than overwriting it

Alternative considered: delete live directories and recreate them as symlinks every boot. Rejected because it risks destroying user data and violates the “persisted volume is source of truth” rule.

### Separate `/workspace` from `/opt/data`

The runtime should use a distinct persisted `/workspace` volume for repos, build artifacts, downloads, and work items. `/home/hermes/workspace` should be a convenience symlink into that mount.

Alternative considered: store work products under `/opt/data`. Rejected because project churn and build artifacts would pollute Hermes control-plane state, complicate backups, and make pruning risky.

### Support persisted `/nix`, but not as an unsafe empty default volume

The workstation needs persisted `/nix` so Nix profile installs, ad hoc `nix shell` caches, and build outputs can survive rebuilds and restarts. However, previous repo validation already showed that mounting an empty Docker volume over `/nix` on a Nix-built image is unsafe because it can hide the image store and stall startup.

The design should therefore support and document persisted `/nix`, but it should do so with a safe mount strategy rather than blindly declaring an empty Docker `VOLUME /nix`.

Alternative considered: omit `/nix` persistence or declare a default anonymous `/nix` volume. Rejected because the user explicitly wants persistent Nix-installed utilities, and the empty-volume approach is already known to be unsafe for this image family.

### Keep `systemd`, including the custom dashboard services

The workstation should continue with the `systemd` runtime direction for both container-level services and HOME-anchored user services. That includes preserving the custom Ghostship Hermes dashboard stack, such as the dashboard web service and profile terminal routing, under the `systemd` runtime instead of dropping those features while aligning the rest of the environment with Hermes.

HOME-anchored user units under `~/.config/systemd/user` should persist through `/opt/data/home/.config/systemd/user`. Hermes-native `gateway install` should remain the default path for user-service installation where it satisfies the workstation requirements, while the system-level dashboard services remain part of the image-managed runtime.

Alternative considered: revert to `s6` or a wholly custom gateway service layout. Rejected because the workstation is meant to feel native to Hermes and user-managed automation, not like a separate orchestration model.

### Seed into persisted targets, not into ephemeral home paths

Repo-managed defaults for `.agents`, Codex, Gemini, Opencode, OpenSpec, and related agent assets should be copied into the persisted destinations under `/opt/data` and `/opt/data/home`, not into ephemeral image paths under `/home/hermes`.

Alternative considered: seed into `/home/hermes` first and let migration pick it up later. Rejected because it adds unnecessary copy churn and makes volume-first precedence harder to reason about.

### Validate with live Docker persistence probes

The implementation should include local Docker validation that proves:
- default Hermes state survives with reused `/opt/data`
- named profiles survive because `~/.hermes` is persisted through `/opt/data/home/.hermes`
- files under `~/.config` survive because they live under `/opt/data/home/.config`
- `/workspace` survives across container replacement
- Nix-installed tools or build outputs survive when `/nix` is reused with a safe mount strategy

Alternative considered: rely on runtime reasoning and unit tests only. Rejected because the user explicitly wants the persistence theory validated empirically.

## Risks / Trade-offs

- [Hermes default state and HOME-anchored `.hermes` remain distinct on disk] -> Document the split clearly, keep `HERMES_HOME=/opt/data`, and use the `/opt/data/home/.hermes` facade only for HOME-anchored behavior such as profiles and wrappers.
- [Boot migration could accidentally destroy local data if implemented carelessly] -> Make copy-missing semantics mandatory, never overwrite persisted destinations, and require conflict-safe migration logic before replacing live paths with symlinks.
- [Persisted `/nix` can be mis-mounted and break image startup] -> Document the safe mount strategy explicitly and validate it locally rather than relying on a fresh anonymous Docker volume over `/nix`.
- [Systemd user services depend on the symlinked home facade being repaired correctly before startup] -> Repair persisted home links first, then start the `hermes` user manager and any user units.
- [Project/build churn can still grow large over time] -> Keep `/workspace` separate from `/opt/data` and document cleanup expectations without touching control-plane state.

## Migration Plan

1. Rewrite the active change contract from `/home/hermes` persistence to the new `/opt/data` + `/workspace` + `/nix` model.
2. Update the image/runtime environment to keep `HERMES_HOME=/opt/data`, add `/workspace`, and prepare the `/opt/data/home` facade.
3. Implement non-destructive boot migration and symlink repair for the selected home directories.
4. Re-root seeding, managed app installs, updater state, and user `systemd` units into the persisted destinations.
5. Update docs and runtime guidance to describe `/opt/data` as the canonical persistent root, `/workspace` as the persisted work area, and `/nix` as the persisted package/build state.
6. Validate reused `/opt/data`, `/workspace`, and `/nix` with local Docker tests before continuing implementation.

## Open Questions

- Which exact home directories should be part of the boot-managed symlink set on day one beyond `.hermes`, `.config`, `.local`, `.cache`, `.agents`, `.codex`, `.gemini`, and `.opencode`?
- What safe `/nix` mount strategy should become the documented default for this image: host bind mount, pre-seeded named volume, or another approach?
- Which workspace convenience paths should the home facade expose by default beyond `/home/hermes/workspace`?
