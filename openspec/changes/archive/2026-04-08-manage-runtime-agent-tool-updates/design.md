## Context

The current image is Nix-first for the system closure but already relies on persisted user state under `/home/hermes` for Hermes profiles, auth, XDG state, and later-installed tools. That means the cleanest long-term model is not a larger system closure, but a smaller one.

This proposal shifts the image toward a minimum-system-viable contract:

- the system layer boots the container and supervises services
- the `hermes` user profile owns updateable user-facing tooling
- a persisted npm prefix owns the fastest-moving agent CLIs and keeps them configured where Hermes can actually invoke them

## Rollout Strategy

### Phase 1: Live-image convergence

Use the running image/container as the proving ground.

Goals for the live image:

1. Move Hermes and the user-facing CLI toolchain to updateable user-managed state.
2. Install the fast-moving npm CLIs where Hermes expects them, with `opencode` treated as a first-class supported tool alongside `codex`.
3. Add the Home Assistant dependency support Hermes expects.
4. Get `hermes -p <profile> doctor` mostly clean for the supported features.
5. Confirm with the operator that the resulting runtime behavior is correct.
6. Confirm ttyd visually matches the dashboard theme in the live image.

### Phase 2: Repo backport

Once the live image is validated, codify the exact proven contract in the repo:

- minimal system package set
- user-profile package bootstrap/update behavior
- npm prefix/update behavior
- service ordering and PATH contract
- docs/changelog/spec updates
- pushed image publication

This avoids baking speculative behavior into the image definition.

## Layer Model

```text
IMMUTABLE SYSTEM LAYER
  - init/runtime helper
  - systemd/unit wiring
  - dashboard
  - router
  - ttyd
  - minimum libs/support required to boot

USER NIX PROFILE LAYER
  - hermes
  - git
  - curl
  - jq
  - python3
  - nix
  - ripgrep
  - nodejs/npm
  - other operator-facing stable CLIs

PERSISTED NPM LAYER
  - @openai/codex
  - @google/gemini-cli
  - opencode-ai
  - agent-browser
```

This model keeps the base image small and makes the actual agent toolchain updateable in place. In particular, `codex`, `gemini`, `opencode`, and `agent-browser` must not merely exist somewhere on disk; they must be discoverable from the Hermes runtime environment, configured so Hermes can invoke them normally, and available in the locations Hermes checks at startup and during `doctor`.

## Nix Daemon Availability

Because the runtime contract depends on `nix profile install` and `nix profile upgrade` inside the container, the Nix daemon path cannot be treated as optional. The live-image phase and the repo backport must ensure `nix-daemon.socket` is available in-container and started before any user-profile convergence runs.

That requirement applies to both:

- boot-time convergence of the `hermes` user profile
- the daily refresh flow for the user-profile package layer

## ttyd Visual Integration

The terminal surface should feel like part of the Hermes dashboard rather than a visually separate embedded app. As part of the live-image validation and repo backport, ttyd should use the same blue theme tokens as the dashboard for its background/accent/chrome treatment so switching between the home view and active terminals feels visually continuous.

This is intentionally scoped to theme-token alignment, not a full terminal UX redesign.

## Managed Updater

After the live-image phase proves the approach, the repo image should gain managed update flows that run on boot and daily.

### Responsibilities

1. Ensure the persisted user-profile and npm-prefix directories exist.
2. Ensure the Nix daemon socket is available before invoking any user-profile operations.
3. Ensure Hermes and the stable user-facing CLI set are installed in the `hermes` user Nix profile.
4. Run `nix profile upgrade` for those user-installed packages, including Hermes itself.
5. Refresh the managed npm CLI set to the latest published versions:
   - `@openai/codex`
   - `@google/gemini-cli`
   - `opencode-ai`
   - `agent-browser`
6. Record success/failure so the last working local tools remain in place if a refresh fails.

## Hermes Updateability

Hermes itself should be treated as part of the user-facing toolchain, not as a permanently fixed image-owned package.

That implies:

- long-running services should execute Hermes from a stable user-facing path rather than assuming only the image closure copy exists
- the boot updater must ensure `nix-daemon.socket` is active and Hermes is present before profile services start
- daily refresh may upgrade Hermes in the user profile, with restart policy handled deliberately rather than implicitly during active conversations

This is the most important architectural shift in the proposal.

## Home Assistant Support

Upstream Hermes treats Home Assistant as an optional extra rather than a built-in baseline dependency. The live-image phase should identify the exact dependency set Hermes expects and validate it, then the repo backport should decide whether that support belongs in the immutable system layer or the managed user profile layer.

## Doctor Hygiene

We should only clear doctor warnings for features we actually intend to use.

### In scope

- Hermes itself being installed and updateable where the runtime expects it
- `openai-codex` CLI/provider path
- `opencode` CLI path and runtime availability
- `agent-browser`
- GitHub API rate limits via `GITHUB_TOKEN`
- Home Assistant optional dependency support

### Out of scope

- `moa`
- RL
- image generation
- generic web-search providers not currently chosen
- arbitrary third-party integrations

This keeps the image honest instead of gaming doctor output.

## Auth and Config Contract

Hermes-native profile auth remains authoritative. Operators should continue using:

- `hermes -p assistant model`
- `hermes -p operations model`
- `hermes -p supervisor model`

for Codex login/model selection.

The proposal does not change the per-profile auth layout Hermes is actually using today.

## Risks

### Boot becomes more dependent on user-state convergence

If Hermes itself lives in the user profile, the updater/bootstrap ordering becomes critical. The proposal must guarantee that `nix-daemon.socket` is available and that the user profile is ready before any Hermes-dependent service starts.

### Daily Hermes upgrades can be disruptive

If Hermes is updateable in place, service restart policy and upgrade timing must be designed carefully so a daily refresh does not interrupt active conversations unexpectedly.

### Live-image changes can drift from the repo

That is intentional during Phase 1, but the change is not complete until the proven live contract is backported into the repo and published.
