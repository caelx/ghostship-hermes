## Context

`ghostship-hermes` currently ships a NixOS-based managed image that bootstraps one repo-owned Hermes agent under `/home/hermes/.hermes`, rewrites `.env` and config at boot, converges user tooling, and supervises the runtime through repo-specific service wiring. That model gives strong declarative control, but it conflicts with the target operating model:

- operators want to manage Hermes inside the container as if it were a native workstation install
- Hermes state must survive container restart and replacement
- user-installed tooling must persist, especially Nix-installed userland tools under `/nix`
- the browser surface should be upstream Hermes, not a separate repo dashboard
- the repo must still keep its product deltas: the local router, the Discord free-channel router pin, and a browser console tab

This is a cross-cutting change. It alters the OS base, service supervision, persistence model, environment-variable ownership, utility packaging, browser contract, build pipeline, smoke tests, and downstream operator documentation.

## Goals / Non-Goals

**Goals:**

- Publish a custom `ubuntu:24.04` workstation image instead of the current NixOS image.
- Keep Hermes core immutable and image-owned under `/opt/hermes`.
- Persist `/home/hermes`, `/workspace`, and `/nix` across restart and container replacement.
- Use `s6` as the in-container supervision layer for the mandatory gateway, dashboard, and router services.
- Keep Hermes management host-native at the config/state level: operators manage Hermes through the CLI, dashboard, and files in persisted home state rather than through image rebuilds.
- Use the upstream Hermes dashboard, with only a small repo-owned patch for a `ttyd`-backed `Console` tab.
- Keep the router mandatory and preserve the Discord free-channel router-pinning patch.
- Split the old utility set into minimal immutable core tools, default userland Nix tools, and native-package-manager userland tools.
- Ship explicit downstream documentation for persistence, `/nix` reuse, home-directory persistence, and operator-facing environment variables.
- Rework GitHub Actions and release docs around the new image.

**Non-Goals:**

- Preserve the NixOS module as the authoritative runtime configuration model.
- Preserve `systemd --user` or `hermes gateway install` as the container service-management contract.
- Keep the repo-owned dashboard implementation or its old MMX/HUDUI API surface.
- Keep the current boot-time projection of container env into `/home/hermes/.hermes/.env`.
- Make the workstation image a general-purpose mutable root image for `apt install` at runtime.
- Keep every previously baked convenience CLI in the immutable core image.

## Decisions

### 1. Build a custom Ubuntu 24.04 workstation image instead of extending the stock runtime image

The new runtime will use `ubuntu:24.04` as the base image and will assemble the repo contract explicitly: Hermes core under `/opt/hermes`, baked-in Nix, the router, the dashboard patch, `ttyd`, `s6`, and only the minimum system/runtime dependencies.

Why:

- matches the desired “native Linux workstation in a container” operator model better than NixOS
- avoids fighting the stock upstream `/opt/data` home/state contract
- makes the base image own only the OS, Hermes core, and mandatory product surfaces
- keeps the repo in control of the small upstream deltas it actually wants to retain

Alternatives considered:

- Use the current NixOS image. Rejected because it preserves the declarative managed-runtime mismatch the user wants to remove.
- Use the stock `nousresearch/hermes-agent` image. Rejected because it keeps the wrong home/state contract and does not cleanly support the desired persistent `/nix` userland layer.
- Use Debian 13. Rejected because Ubuntu 24.04 is the explicit target, while still remaining close to normal upstream Linux expectations.

### 2. Make `/home/hermes`, `/workspace`, and `/nix` the persisted downstream contract

The workstation will treat:

- `/home/hermes` as the canonical persisted home and Hermes state root
- `/workspace` as the persisted work-products root
- `/nix` as the persisted userland Nix store/profile root

The image will not hide those requirements behind symlink facades such as `/opt/data/home`. `HOME` and `HERMES_HOME` will point directly into the persisted home tree.

Why:

- matches the desired native operator mental model
- keeps Hermes state, XDG state, npm config, CLI auth, and dotfiles in one persisted mount
- makes `/nix` persistence explicit instead of accidental

Alternatives considered:

- Keep `/opt/data` as the main persisted root. Rejected because it reintroduces the upstream container contract the user explicitly wants to move away from.
- Persist only `~/.hermes` and leave the rest of home ephemeral. Rejected because the user wants broader workstation persistence, not a narrow app-state mount.

### 3. Document and support a safe `/nix` persistence flow instead of treating `/nix` as a blind bind mount

The new docs must explicitly distinguish two supported downstream patterns:

- recommended named-volume reuse for `/nix`
- explicit one-time seeding for bind-mounted `/nix`

The runtime contract must warn that mounting a brand-new empty `/nix` over an image that already contains Nix can hide the image’s store contents. The image therefore needs a documented seeding path for `/nix`, and the docs must show how downstream reuses the same `/nix` volume across container rebuilds and image upgrades.

Why:

- `/nix` persistence is a non-negotiable requirement
- operators need a repeatable procedure for both restart and replacement
- “just mount `/nix`” is not good enough when the image itself depends on Nix

Alternatives considered:

- Do not persist `/nix`. Rejected by requirement.
- Persist only per-user Nix profiles under home. Rejected because the requested contract explicitly includes `/nix`.

### 4. Use `s6` for in-container service supervision and Docker for container lifecycle

The container will use `s6` as PID 1 and supervise the mandatory long-running services:

- Hermes gateway
- Hermes dashboard
- Ghostship router

The `ttyd` integration will be owned by the dashboard patch path rather than by a separate always-on system manager contract. Docker remains the outer lifecycle manager, and `hermes gateway install` is not part of the container contract.

Why:

- supports the desired workstation container with multiple long-running processes
- avoids reintroducing `systemd --user` or a pseudo-host init stack
- keeps restart semantics clear: Docker restarts the container, `s6` restarts the in-container services

Alternatives considered:

- Keep `systemd --user`. Rejected because it preserves the service-management mismatch even if Hermes config becomes more native.
- Run everything from a single wrapper shell script. Rejected because the service graph is too important for ad hoc supervision.

### 5. Keep Hermes config ownership downstream-owned and make the image own only fixed filesystem/process env

The new env contract splits into two classes.

Image-owned fixed env:

- `HOME=/home/hermes`
- `HERMES_HOME=/home/hermes/.hermes`
- `XDG_CONFIG_HOME=/home/hermes/.config`
- `XDG_CACHE_HOME=/home/hermes/.cache`
- `XDG_DATA_HOME=/home/hermes/.local/share`
- `NPM_CONFIG_PREFIX=/home/hermes/.local`
- `PATH` including `/opt/hermes/bin`, the default/user Nix profile bin path, and `/home/hermes/.local/bin`

Downstream-owned operator env:

- provider credentials and model/runtime settings
- Discord inputs
- router env
- browser/CDP inputs
- webhook inputs
- approved utility/service env such as Bitwarden access

The image must not rewrite `/home/hermes/.hermes/.env` on boot. Instead, docs must describe two supported downstream patterns:

- pass env directly through `docker run` / Compose `environment` or `env_file`
- persist an operator-managed `/home/hermes/.hermes/.env` inside the mounted home volume

Why:

- this is the cleanest native-like behavior
- it keeps the container from fighting operator edits
- it makes the downstream deployment contract explicit instead of hiding it in bootstrap behavior

Alternatives considered:

- Keep rewriting `.env` from container env at boot. Rejected because it preserves the managed-runtime projection model the user wants to leave behind.

### 6. Make the upstream dashboard the source of truth and carry only a small repo-owned `Console` tab patch

The browser surface will come from the upstream Hermes dashboard on its native runtime path. The repo keeps only a narrow patch set:

- add a `Console` tab or nav entry
- expose or proxy the minimal backend path needed to create and reach `ttyd` sessions
- keep the `ttyd` integration same-origin with the dashboard

The repo will not keep the old custom dashboard backend/frontend or its browser API contract.

Why:

- reduces browser drift materially while still preserving the required console UX
- keeps the patch small and easy to audit against upstream
- avoids maintaining a second full dashboard stack

Alternatives considered:

- Keep the custom dashboard. Rejected because the user explicitly wants the built-in dashboard.
- Wrap the upstream dashboard inside a larger Ghostship shell. Rejected because it recreates a parallel dashboard product.
- Inject UI changes at runtime. Rejected because it is too fragile.

### 7. Split the utility surface into immutable core, default userland Nix, and native-package-manager layers

The immutable core image will contain only:

- Ubuntu base OS
- Hermes core
- Nix
- Node/npm as the native package-manager path for Node-based agent tools
- `s6`
- `ttyd`
- router/dashboard patch runtime dependencies
- only the shell/process/network utilities directly required for boot, health checks, and core services

Default userland Nix will contain the repo-approved generic Linux/operator tools that should be available by default but do not belong in the immutable core image, such as:

- `gh`
- `ssh`, `scp`, `ssh-keygen`
- `gcloud`
- `gws`
- `bws`
- `git`
- `jq`
- `ripgrep`
- `fd`
- `yq`
- `tmux`

Native package-manager userland will cover tools that are best managed by their own ecosystem, especially npm-managed agent CLIs such as:

- `codex`
- `gemini-cli`
- `opencode`

The design assumption is first-run seeding of the default userland layers into persisted storage, not continuous repo-owned convergence of all user tooling on every boot.

Why:

- satisfies the “move as much as possible out of core” goal
- preserves default availability of approved operator tools
- keeps ecosystem-native update flows where they make more sense than Nix

Alternatives considered:

- Keep all old tools in the immutable image. Rejected because it keeps the base too large and muddy.
- Force all userland tools through Nix. Rejected because the user explicitly wants native package managers for Node-native CLIs.

### 8. Keep the router and Discord router pin as mandatory repo-owned deltas

The local router remains a mandatory core service in the final image, and the repo continues to patch Hermes so configured Discord free-response channels stay pinned to the router-managed path.

Why:

- these are explicit product requirements, not optional add-ons
- upstream still does not expose a declarative per-channel routing override that replaces the repo patch

### 9. Rebuild GitHub Actions and release docs around the Ubuntu workstation image

The repo’s CI/publication path will stop treating the NixOS final image derivation as the canonical published artifact. Instead, Actions will build, smoke-test, and publish the new Ubuntu 24.04 workstation image for both supported architectures, and the release/runbook docs will explain the new persistence and env contract.

Why:

- the image build architecture is changing materially
- docs and publish workflows must agree on the same operator contract

## Risks / Trade-offs

- [Risk] Losing declarative NixOS convergence makes runtime drift easier inside persisted home state. → Mitigation: keep Hermes core immutable, keep the repo-owned patch set small, and document which layers are operator-owned versus image-owned.
- [Risk] `/nix` persistence is easy to get wrong and can break first boot if mounted unsafely. → Mitigation: make `/nix` seeding and reuse a first-class documented contract with explicit named-volume and bind-mount instructions.
- [Risk] Carrying a `Console` tab patch means the dashboard is not purely upstream. → Mitigation: keep the patch small, source-compatible, and narrowly scoped to the console route/tab only.
- [Risk] Default userland tooling may no longer be instantly available if the first-run seed path is broken. → Mitigation: validate the seed path in smoke tests and keep the default tool list explicit and small.
- [Risk] Moving default tools out of the immutable image changes long-standing operator expectations. → Mitigation: document the new split clearly, including where each tool class lives and how to reinstall or upgrade it.
- [Risk] GitHub Actions migration from the NixOS image path to the Ubuntu workstation image can break multi-arch publication or cache reuse. → Mitigation: keep the publication contract explicit, test both architectures, and update the runbook at the same time as the workflow change.

## Migration Plan

1. Land the contract changes in OpenSpec, docs, and AGENTS memory before implementation starts.
2. Build the Ubuntu 24.04 workstation image with Hermes core, Nix, Node/npm, router, `ttyd`, and `s6`.
3. Replace the current NixOS bootstrap/runtime wiring with the new persisted-home and persisted-`/nix` contract.
4. Replace the custom dashboard with the upstream dashboard plus the small `Console` tab patch.
5. Move default extra CLIs into the seeded userland Nix layer and npm-managed layer.
6. Rewrite smoke tests and live validation around the new runtime, persistence, and env contract.
7. Update GitHub Actions build/publication and release docs together.
8. Roll out through a test image first; rollback is to keep publishing the existing NixOS image contract until the Ubuntu workstation image passes publish and live validation.

## Open Questions

- Should the repo keep publishing a separate reusable base artifact in addition to the final workstation image, or only the final image?
- What exact user-profile path should the docs standardize for the default userland Nix profile: `~/.nix-profile`, an XDG profile path, or a dedicated repo-owned profile name?
- Should the first-run default userland tool seeding be fully automatic, or should the repo expose an explicit initialization command for downstream operators who want tighter control?
- Does the upstream Hermes dashboard patch land best in the wrapped Hermes package, or should the repo carry a separate patching step in the image assembly path?
