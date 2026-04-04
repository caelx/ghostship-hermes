## Context

The current image behaves like a Ghostship-managed agent workstation layered on top of Hermes. It bootstraps Hermes with a large shell runtime, seeds repo-managed skills and develop-environment defaults into persisted state, installs and refreshes Codex/Gemini/Opencode/OpenSpec tooling, carries honcho compatibility behavior, and exposes a profile-aware browser dashboard backed by persistent per-profile `ttyd` services.

That is now the wrong center of gravity. The new target is to align with upstream Hermes as closely as possible, especially the upstream Nix flake and NixOS module container-mode semantics. The user's clarified constraints are:

- upstream alignment takes priority over preserving Ghostship-specific runtime behavior
- if the container expects `HERMES_HOME` under `/data`, use `/data`
- keep all `ghostship-*` utilities installed
- remove all custom skills, including repo-managed Ghostship skills and vendored skills, plus custom plugins, honcho behavior, and Ghostship-managed agent app install/update loops
- keep only a minimal dashboard with on-demand non-persistent `ttyd` sessions
- if the image uses a dedicated `hermes` user, make it UID/GID `3000:3000`
- first implementation work must be a minimal declarative container spike used to discover the correct runtime paths, user behavior, and persistence contract before the full rebuild proceeds

The upstream Hermes module and docs split responsibilities differently than the current image:

- declarative config lives in Nix and is written into `HERMES_HOME`
- the upstream managed runtime marks Hermes as managed and blocks live config mutation through the normal CLI path
- container mode is the upstream path for a mutable user environment
- upstream container mode uses `/data` for state, `/home/hermes` for HOME, and binds `/nix/store` from the host

Our shipped GHCR image is not the same topology as upstream "NixOS host launches an inner mutable Ubuntu container", so the design must align with upstream Hermes contracts without copying the entire host-managed deployment shape verbatim.

## Goals / Non-Goals

**Goals:**
- Rebuild the image around upstream Hermes Nix/container-mode semantics rather than the current Ghostship runtime bootstrap layer.
- Make `/data` the canonical persisted Hermes root and keep `/home/hermes` as the user home facade.
- Prove the runtime contract early with a minimal declarative Hermes container that boots successfully and exposes a usable terminal surface.
- Preserve broad common HOME-backed persistent state under `/data/home`, not only a small package-specific subset.
- Preserve `/workspace` and persisted `/nix`, and explicitly validate user-level `nix profile install` persistence across container replacement.
- Keep the image lean: upstream Hermes essentials, runtime Nix support, `ttyd`, the minimal dashboard stack, and all `ghostship-*` utilities.
- Keep Hermes built-in skills untouched while removing Ghostship-managed and vendored default skill seeding.
- Keep only the smallest Ghostship-specific browser surface required for operator convenience.
- Carry the work through the final image build, full runtime validation, cleanup, and a locally running container that is ready for manual dashboard inspection.

**Non-Goals:**
- Recreating the current workstation model with auto-updated agent apps, mutable asset refreshers, or profile reconciliation.
- Maintaining compatibility with `/opt/data` as the canonical state root.
- Preserving honcho compatibility behavior or old profile-aware browser workflows.
- Giving Hermes self-authority to apply the system flake or run `nixos-rebuild` inside the default runtime.
- Designing a rich browser UI in this change; the dashboard only needs to be minimal and functional.

## Decisions

### 1. Use upstream Hermes Nix/container-mode semantics as the primary runtime contract

The rebuilt image will follow upstream Hermes expectations wherever practical:

- `HERMES_HOME=/data/.hermes`
- `HOME=/home/hermes`
- declarative config written into `HERMES_HOME`
- managed/runtime behavior centered on Hermes' own flake/module model

Why:
- This reduces bespoke Ghostship runtime logic.
- It makes runtime behavior easier to reason about against upstream docs and source.
- It narrows the amount of Ghostship-owned code that must be maintained across upstream Hermes releases.

Alternatives considered:
- Keep `/opt/data` as the canonical state root and adapt Hermes around it.
  - Rejected because the user explicitly asked to use `/data` if that is what Hermes expects.
- Reuse the existing Ghostship runtime wrapper and slowly strip pieces out.
  - Rejected because the old wrapper already encodes the assumptions we are removing.

### 2. Keep a thin home facade, but move the canonical persisted roots to `/data`, `/workspace`, and `/nix`

The runtime will keep a thin facade at `/home/hermes`, backed by persisted state under `/data/home`. The canonical persisted roots become:

- `/data` for Hermes state
- `/data/home` for HOME-backed persistent user state
- `/workspace` for repos, work products, and operator-owned working files
- `/nix` for persistent Nix-managed package/build state

Upstream Hermes profile management adds one important nuance: named profiles are anchored to `~/.hermes/profiles/...` regardless of the active `HERMES_HOME`. The rebuilt runtime therefore persists `~/.hermes` through `/data/home/.hermes` while still keeping the canonical managed default state at `/data/.hermes`.

`HERMES_HOME` remains explicitly separate from the persisted home facade. Hermes state must continue to live at `/data/.hermes`, and the `/home/hermes` facade must not shadow, relocate, or merge that state into the general HOME-backed persistence tree.

At minimum, the rebuilt image must persist broad common home directories such as:

- `~/.config`
- `~/.local`
- `~/.cache`

It must also preserve the HOME-backed config/state locations that user-installed coding-agent tools are expected to use after they are added later, even though those tools are no longer preinstalled in the base image. That includes keeping stable persistence for both:

- common XDG-backed config/state roots used by later-installed tools
- known agent-specific home directories when they are present, such as `~/.agent-browser`, `~/.agents`, `~/.codex`, `~/.copilot`, and `~/.gemini`

Additional top-level user-managed toolchain and credential roots that should remain persistent when present include:

- `~/.npm`
- `~/.bun`
- `~/.ssh`
- `~/.gnupg`
- `~/.pki`

For mutable user-level Nix operations, the runtime also needs a working daemon socket on the persisted `/nix` mount. The image therefore prepares `/nix/var/nix/daemon-socket` during storage setup and starts `nix-daemon.socket` only after that path exists, so `nix profile install` works for the `hermes` user in the steady-state container.

The first validation spike will inspect actual runtime writes and confirm the minimum top-level persistence set. Subpaths such as `~/.config/opencode`, `~/.config/browseruse`, `~/.local/share/opencode`, `~/.local/state/opencode`, `~/.cache/opencode`, `~/.cache/ms-playwright`, and `~/.cache/puppeteer` remain important validation examples, but they are covered by persisting their required top-level parents.

Persistence in this design means "survive restart and container replacement", not "freeze code forever". For later-installed tools, the persisted home contract must preserve the files the tools use, while still allowing their code and dependencies to be updated in place by the tool's own package manager or by user-level Nix operations. The runtime must not re-seed old image copies over those persisted tool roots on boot.

Why:
- This preserves broad user state instead of only a small hand-picked set of package dirs.
- It separates "not preinstalled by default" from "not supported as persistent user state later".
- It still provides an explicit separation between Hermes state, user HOME state, work products, and Nix state.
- It avoids interfering with upstream Hermes assumptions about the structure and ownership of `HERMES_HOME`.

Alternatives considered:
- Mount only `~/.hermes` and a few package-specific directories.
  - Rejected because the user wants persistence for common home config broadly, not narrow package-specific exceptions.
- Collapse all state into a single mounted `/home/hermes`.
  - Rejected because it blurs the distinction between Hermes state, HOME state, and work products, and makes migration/inspection less clear.

### 3. First implementation work is a minimal declarative bootstrap spike

The change will begin by building a minimal image that:

- uses upstream Hermes-oriented config and paths
- starts Hermes gateway successfully with the smallest viable declarative config
- exposes a minimal shell/terminal access path
- allows runtime inspection of user identity, paths, and write locations

The spike will be used to answer these questions before the full rebuild proceeds:

- does the runtime cleanly support `hermes` as UID/GID `3000:3000`?
- what exact paths Hermes writes under `HERMES_HOME` and `HOME`?
- what persistent home directories should the image preserve by default?
- does persisted `/nix` support `nix profile install` across container replacement?

Why:
- This avoids redesigning around assumptions inherited from the current image.
- It gives the final design a verified path contract instead of a speculative one.

Alternatives considered:
- Perform the full rewrite immediately and test after the fact.
  - Rejected because the persistence/user/path contract is central and currently under change.

### 4. If a dedicated `hermes` user is used, it will be `3000:3000`

The rebuilt image will keep the dedicated `hermes` identity only if it can be done cleanly while staying upstream-aligned. If used, it will be UID/GID `3000:3000`.

Why:
- The user explicitly requested this.
- A stable numeric identity simplifies host-volume ownership and operational expectations.

Alternatives considered:
- Use upstream name-only defaults without pinning UID/GID.
  - Rejected because the user explicitly requested `3000:3000` when a `hermes` user is present.

### 5. The image package set becomes lean and declarative

The rebuilt image will keep:

- upstream Hermes
- runtime Nix support
- `ttyd`
- the minimal dashboard/proxy stack
- all `ghostship-*` utilities

The rebuilt image will remove from the default image package set:

- Codex
- Gemini CLI
- Opencode
- OpenSpec
- `skills`
- vendored Google Workspace CLI and skills
- Bitwarden CLI
- `feed`
- Ghostship-managed mutable app/asset refresh machinery

Why:
- The user wants a small image and wants Hermes to manage its own packages rather than shipping a curated workstation stack.
- Removing these packages also removes the need for the current update timers, seed trees, and runtime wrappers built around them.

Alternatives considered:
- Keep the current broad tool bundle but stop auto-updating it.
  - Rejected because it still leaves the image opinionated and heavy.

### 6. Keep only a minimal dashboard with on-demand ephemeral `ttyd`

The browser surface will be reduced to:

- a small static HTML page
- actions that launch and close a `ttyd` session on demand
- no persistent `ttyd` systemd services
- no profile reconciler loop
- no profile-specific browser routes that require background orchestration

Why:
- This preserves a convenient browser entrypoint without carrying the current custom service graph.
- It matches the user's requirement for the smallest possible dashboard behavior.

Alternatives considered:
- Remove the dashboard entirely.
  - Rejected because the user still wants a browser dashboard.
- Preserve the existing profile-aware dashboard.
  - Rejected because it encodes the current custom architecture being removed.

### 7. Ghostship-managed skill and asset seeding is removed

The rebuilt image will stop seeding:

- repo-managed local skills, including Ghostship-specific skills
- vendored Google Workspace skills
- `.codex`, `.gemini`, `.opencode`, and related develop-environment content

Hermes built-in skills remain untouched because they are part of upstream Hermes behavior.

Why:
- The user explicitly wants all custom skills removed while leaving Hermes built-ins alone.
- Removing seeding also removes a large amount of path migration and non-destructive copy logic from the current runtime.

Alternatives considered:
- Keep the seed machinery but make it optional.
  - Rejected because the goal is removal and upstream alignment, not another configurable custom layer.

### 8. Declarative Hermes config remains host/image owned; user-level Nix remains runtime mutable

The rebuilt image will treat Hermes config as declarative and image-owned, while still allowing user-level Nix operations in the persisted runtime state.

That means:

- `services.hermes-agent`-style configuration is the source of truth for default Hermes config
- runtime validation must prove user-level `nix profile install` works and persists with reused `/nix`
- the default runtime does not permit Hermes to self-apply the system flake

Why:
- This keeps the base system stable and reviewable.
- It still gives Hermes and operators a mutable user-level Nix tool surface.

Alternatives considered:
- Allow Hermes to run `nixos-rebuild` or self-apply the flake.
  - Rejected for this change because it greatly increases privilege and failure risk and is not required for the desired container behavior.

## Risks / Trade-offs

- **[Upstream container mode and shipped-image topology differ]** → Validate the minimal image early and adapt only the thinnest necessary compatibility layer.
- **[Switching to `/data` is breaking for existing persisted state]** → Document the new volume contract and include explicit migration guidance in docs and tasks.
- **[Broad home persistence can capture more state than the current image]** → Limit default persisted directories to common user-state roots justified by validation, and document single-writer assumptions clearly.
- **[Removing preinstalled utilities can surprise current users]** → Treat the package-set reduction as a breaking change and document exactly what remains in the image.
- **[Using `3000:3000` may conflict with upstream assumptions or volume ownership edge cases]** → Make it part of the first validation matrix and adjust only if the runtime proves it cannot work cleanly.
- **[Minimal dashboard may still need more runtime glue than expected]** → Keep the browser feature set intentionally narrow and test-driven.

## Migration Plan

1. Create the minimal upstream-aligned container spike with declarative Hermes config and no reuse of the old Ghostship runtime bootstrap.
2. Boot the spike with persisted `/data`, `/workspace`, and `/nix`, then inspect the runtime environment, write paths, and user identity.
3. Validate `nix profile install` persistence across container replacement with reused `/nix`.
4. Finalize the new persistence contract for `/data`, `/data/home`, `/workspace`, and `/nix` based on the spike findings.
5. Replace the current image/runtime wiring with the new upstream-aligned package set and runtime structure.
6. Reintroduce only the minimal dashboard and on-demand `ttyd` behavior required by the new specs.
7. Remove obsolete seeding, updates, honcho, profile reconciliation, and preinstalled non-ghostship workstation tools.
8. Update docs, tests, AGENTS guidance, and change log to match the new runtime model.

Rollback strategy:

- Until the rebuild is merged, the existing image remains the operational fallback.
- During implementation, the minimal spike should be kept separately verifiable so regressions in the full rebuild can be isolated quickly.

## Open Questions

- Which static file server/proxy is the smallest acceptable choice for the minimal dashboard surface: keep Caddy, or replace it with an even smaller stack?
- Beyond `.config`, `.local`, and `.cache`, which additional HOME-backed directories should be persisted by default after the discovery spike?
- Should the final image expose only the default Hermes profile in the browser surface, or should the dashboard support selecting arbitrary Hermes profiles without persistent per-profile services?
