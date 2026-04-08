# Agent Directives: ghostship-hermes

## Purpose

- Build and publish `ghcr.io/caelx/ghostship-hermes`: a GHCR container image for Hermes with a lean upstream-aligned runtime plus the repo's `ghostship-*` service utilities.
- Treat this repo as a monorepo for the Hermes image and Python CLI utilities.

## Project Invariants

- Run Hermes as a non-root runtime user. Do not grant general `sudo` in-container.
- Include Nix in the runtime for ad hoc `nix shell` usage.
- Keep `HOME=/home/hermes` and use a persisted `/home/hermes` volume as the canonical runtime state mount.
- Keep the managed Hermes state under `/home/hermes/.hermes` by setting the Hermes NixOS module `stateDir` to `/home/hermes`, and keep `/workspace` as the separate persisted work-products mount.
- Persist `/nix` whenever the deployment expects user-installed Nix software or build outputs to survive container replacement, but do not hide the image store behind a brand-new empty Docker volume.
- Default browser entrypoint is the minimal dashboard controller on port `7681`, serving the static UI and proxying same-origin `ttyd` terminals directly.
- Keep CLI access available for admin and debug workflows.
- Discord gateway is a later optional interface, not the v1 default.
- Configure Hermes declaratively through the upstream Hermes NixOS module.
- Keep local package and NixOS documentation available in the image so Hermes can inspect reference material in-container.
- Do not seed Ghostship-managed default skills or develop-environment workstation content into the image runtime.
- Keep the pinned `gws` CLI in the default image, but do not vendor or seed Google Workspace skills.
- Do not preinstall Codex, Gemini CLI, Opencode, OpenSpec, `skills`, or `feed` in the default image; `gws` and `bws` are the approved extra CLIs.
- Keep the browser surface minimal: one dashboard, on-demand ephemeral `ttyd`, no persistent per-profile terminal services.
- Keep the declarative Hermes profile scaffold in the image aligned to `assistant`, `operations`, and `supervisor`, with `assistant` as the sticky default profile.
- Keep one persistent gateway service per declared profile, managed by NixOS systemd units.
- Persist the whole `/home/hermes` tree instead of maintaining a top-level HOME symlink policy for individual dot-directories.
- Keep the first utility scaffold focused on SearXNG.
- Watch upstream Hermes releases and update `packages/hermes-image/hermes-release.txt`.
- Publish multi-arch `amd64` and `arm64` images plus manifest lists for the documented release channels.
- Prefix repo-owned utilities with `ghostship-`.
- All CLI utilities must emit native JSON by default. Do not add table-first or other human-formatted default output.

## CI, Docs, And Release Hygiene

- Build on every push and PR.
- From `main`, publish the full mutable tag set.
- For non-`main` `workflow_dispatch`, publish immutable `sha-*` tags only.
- Keep repo identity and OSS maintenance files present: `README.md`, `LICENSE`, `CHANGELOG.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`, and `.github/` metadata.
- Document how to build and test Python CLI utilities in this repo.
- After Docker-based verification, aggressively prune stale images, dead test containers, temporary artifacts, and unused volumes. Leave at most one retained copy of each needed image plus any still-needed live validation container.
- Keep Docker clean during local validation: remove old `ghostship-hermes*` containers once they are no longer needed instead of letting validation containers accumulate.

## Build And Test Commands

```fish
python3 scripts/python_utility.py lock packages/searxng-cli
python3 scripts/python_utility.py test packages/searxng-cli
python3 scripts/python_utility.py build packages/searxng-cli
nix build .#packages.x86_64-linux.ghostship-hermes-runtime
nix build .#packages.aarch64-linux.ghostship-hermes-image
```

## Shared CLI Contract

- Keep `ghostship-*` command names aligned with API and client operation names. Do not add compatibility aliases. Use generic passthrough commands like `request` or `call` only as fallback escape hatches.
- Honor a default hard timeout of `30` seconds via `--timeout`.
- Use the shared JSON error and exit-code envelope.
- Expose `--dry-run` on write and delete commands so agents can inspect the exact request object before mutation.
- In `BaseHttpClient.request_json()`, call the base transport path directly with `BaseHttpClient.request(self, spec)`. Do not route through service overrides like `self.request(spec)`.

## Durable Lessons

### Hermes Runtime

- Hermes has no documented primary web UI today; the official UX is CLI/TUI plus messaging gateway workflows.
- Hermes managed config for the NixOS module lives under `${stateDir}/.hermes`; with this image that means `HERMES_HOME=/home/hermes/.hermes` and `stateDir=/home/hermes`.
- Using `/home/hermes` as the persisted state root is a repo-specific deviation from upstream container-mode docs, which otherwise separate state and HOME. Keep calling that out explicitly when it matters.
- Upstream Hermes profiles are anchored to `~/.hermes/profiles/...`; with `stateDir=/home/hermes`, the managed default profile and the named profile tree now live together under `/home/hermes/.hermes`.
- A minimal declarative gateway config is enough to boot the Hermes service even before operator-specific provider or messaging settings are added.
- Upstream Hermes does not expose named profiles as a declarative NixOS-module option. Precreating `assistant`, `operations`, and `supervisor` from Nix and supervising each one with its own gateway service is an approved repo-specific deviation and should stay implemented as NixOS-managed units, not as mutable runtime drift.
- The browser dashboard should treat terminals as ephemeral tabs: opening spawns a fresh `ttyd` session focused on `/home/hermes`, closing removes only that session, and zero sessions returns the UI to a blank home state.
- The dashboard proxies ttyd from its own origin on `:7681`; do not turn ttyd `--check-origin` back on for proxied sessions or tab switches will fall into ttyd's reconnect overlay.
- The ttyd proxy must stream decoded HTTP bytes and preserve websocket subprotocol negotiation; stripping `content-encoding` while forwarding raw gzip bytes or accepting the browser websocket before upstream subprotocol negotiation will break the embedded terminal.
- The image should bootstrap `assistant`, `operations`, and `supervisor` profiles so operators can inspect the upstream `~/.hermes/profiles/...` layout immediately after boot, with `assistant` set as the sticky default profile.
- The bootstrap oneshot should materialize the approved `assistant`, `operations`, and `supervisor` profiles, preserve shared and per-profile skill plus `SOUL.md` copy-once behavior, write the managed runtime env into each profile `~/.hermes/profiles/<profile>/.env`, and leave config generation shell-only without depending on extra Python packages like PyYAML.
- Managed profile gateways should treat `~/.hermes/profiles/<profile>/.env` as the single operator-facing source of truth via systemd `EnvironmentFile`; if the managed env contract changes, update the bootstrap writer rather than layering more service-level env overrides.
- Profile `.env` should hold the profile-facing runtime contract, including Hermes/provider secrets, browser config, Discord settings, Bitwarden access, and operator-facing `ghostship-*` CLI env. Keep only image infrastructure, router-daemon internals, and container boot plumbing outside profile `.env`.
- Optional runtime skill staging lives under `/home/hermes/seeds/shared/skills/<skill>` for shared skills and `/home/hermes/seeds/profiles/<profile>/skills/<skill>` for profile-specific skills; bootstrap may copy a missing skill directory into Hermes, but it must never overwrite an existing destination skill because Hermes owns it after first seed.
- Upstream Hermes Nix `services.hermes-agent.settings` deep-merges across module definitions and preserves on-disk user-added keys that Nix does not touch; use Nix first for the scaffolded defaults, but let untouched runtime keys survive rebuilds.
- For Hermes auxiliary tasks, setting `base_url` bypasses provider resolution entirely; use a direct endpoint only when you do not want Hermes to keep walking its native auxiliary provider chain for that task.
- The current three-profile scaffold expects `openai-codex/gpt-5.4` as the primary model path via Codex OAuth runtime state, `OPENCODE_GO_API_KEY` for the Hermes-native `opencode-go/minimax-m2.7` fallback, `GOOGLE_AI_STUDIO_API_KEY` for all direct auxiliary tasks, and `BWS_ACCESS_TOKEN` only for Bitwarden-backed workflow secrets.
- Hermes Codex OAuth should be initialized through `hermes -p <profile> model` and stored in `~/.hermes/profiles/<profile>/auth.json`; do not assume root-level `oauth.json` files or `OPENAI_API_KEY` are part of the primary `openai-codex/gpt-5.4` path.
- Run `hermes skills list` once under the Hermes runtime user after first boot to materialize the skills hub directories and lockfile before treating missing skills-state paths as a real bug.
- The scaffold also enables Hermes `memory.provider = holographic` for every profile, with plugin settings under `plugins.hermes-memory-store`; this is local profile-scoped SQLite memory and does not need an extra API key.
- The scaffolded profile `config.yaml` now includes Discord defaults (`require_mention = true`, `auto_thread = true`, `reactions = true`, `group_sessions_per_user = true`), while each gateway service maps profile-specific env vars into Hermes' standard Discord env names so a shared `DISCORD_GENERAL_CHANNEL_ID` stays mention-only and each `DISCORD_<PROFILE>_CHANNEL_ID` becomes a free-response role channel. Hermes still has no native per-profile Discord icon setting; distinct icons require separate Discord bot applications.
- Tirith is intentionally installed in the image runtime and kept on the service PATH so Hermes pre-exec scanning can use `tirith_path = "tirith"` without a bootstrap download. The image also vendors `agent-browser` without preinstalling Chrome or Chromium; the shared scaffold sets `browser.cloud_provider = "local"` so Hermes local browser mode defaults to that CLI unless an operator manually attaches CDP with `/browser connect`. Hermes docs currently describe only a single live CDP attachment via `/browser connect [ws://host:port]`, not a declarative or multi-endpoint CDP config surface. Use `BROWSER_CDP_URL` when you want one persistent remote CDP default. Do not try to model multiple concurrent CDP defaults in Nix; Hermes only documents a single CDP target.
- `ghostship-hermes-router` should reuse Hermes-facing provider env names where a matching backend exists; today that specifically means accepting `OPENCODE_GO_API_KEY` as an alias for the router's OpenCode Zen credential path, while `GOOGLE_AI_STUDIO_API_KEY` remains Hermes-direct until the router grows a native Google provider.

### Container And Supervisor Behavior

- The runtime needs a root init phase to prepare `/home/hermes`, `/home/hermes/.hermes`, `/workspace`, and `/nix` before dropping to the `hermes` user.
- Mounting an empty Docker volume over `/nix` on a fresh Nix-built image is unsafe: it can hide or copy the image store and stall `docker run`.
- Docker validation against a repo-local Nix store must mount that same store root into the container at `/nix`; binding the host `/nix` while the image was built in `.nix-local-store` hides the needed store paths.
- Docker Desktop imports of the NixOS rootfs can fail with `exec /init: no such file or directory` if a WSL bind mount replaces `/nix` before startup; the dashboard smoke test should avoid binding `/nix` unless it is explicitly validating persisted store behavior.
- Imported NixOS images may not expose `bash` through `docker exec bash`; image tests should use `/bin/sh` plus an explicit PATH to the NixOS system profile.
- The docker-container NixOS profile leaves the firewall active inside the container; published dashboard traffic requires explicitly allowing TCP `7681`.
- Persisted `/nix` must include a writable `/nix/var/nix/daemon-socket` path and the image must start `nix-daemon.socket` after storage preparation, or user-level `nix profile install` will fail even though `nix` is installed.
- Persisting `/home/hermes` directly is the supported durability model for this image; it keeps Hermes CLI profiles, managed state, XDG state, and later-installed agent-tool config together in one mount.
- This repo should not accumulate Docker artifacts. After validation, aggressively prune unused images, stopped containers, and unused volumes so Docker keeps only the current needed image set.
- After archiving a change, clean up the Docker artifacts generated for that change's validation work. Default to removing only the containers, images, and volumes created during the task; do a full Docker reset only when the user explicitly asks for it.

### Skill Authoring

- Repo-managed service skills should stay short, trigger-rich, and workflow-oriented: prioritize start-here guidance plus inspect -> dry-run -> mutate -> verify sequences over command dumps.
- Use family-level structure for service wrappers, but keep domain-specific ordering and failure guidance inside each skill instead of mass-applying identical wording.

### Platform And CI

- Scheduled GitHub release polling must authenticate with `GITHUB_TOKEN` or `GH_TOKEN`; anonymous `api.github.com` release queries can hit rate limits and break Actions.
- The Hermes release updater must change both `packages/hermes-image/hermes-release.txt` and the `hermes-agent` flake input/lock; updating only the label file does not change the packaged Hermes build.
- GitHub Actions pushes made with `GITHUB_TOKEN` do not trigger the repo's `push` workflows. If the Hermes release updater commits directly to `main`, it must explicitly dispatch `publish-image.yml` or use a different credential model.
- Hermes `v2026.4.8` expects a `system.activationScripts.setupSecrets` phase in its NixOS module ordering. This repo does not use a separate secrets activation module, so keep a no-op `setupSecrets` compatibility hook in the image module unless the module stack grows a real provider for it.
- The `hermes` user tooling refresh path must upgrade Hermes from an unlocked flake ref such as `github:caelx/ghostship-hermes#hermes-agent-wrapped`; a baked store path can bootstrap the first boot, but `nix profile upgrade --all` cannot move a locked store-path install forward.
- The image-managed `hermes` toolchain now lives in its own Nix profile at `/home/hermes/.local/state/nix/profiles/ghostship-managed`; keep that separation so boot-time convergence does not collide with operator-owned `~/.nix-profile` entries such as older `hermes-agent` installs.
- `ghostship-hermes-startup.service` must not require the mutable user-tooling oneshot for the main runtime to come up; bootstrap and the dashboard/router/profile gateways should keep booting even if tool refresh work fails.
- Hermes is not packaged in the inspected `nixos-25.11` nixpkgs tree, while `ttyd`, `codex`, `gemini-cli`, and `opencode` are.
- Local flake evaluation only sees git-tracked files. Stage new Nix files and vendored trees before relying on `nix flake check` or `nix build` in a worktree.
- On this host, run only one Nix build or eval at a time; overlapping Nix client commands can wedge daemon responsiveness and create misleading validation failures.
- Keep `.nix-local-store/` gitignored. It is repo-local build state for Docker and Nix validation, not source content.
- On the current `x86_64` dev host, `nix flake check` does not build `aarch64-linux` outputs. Use `nix eval` locally to keep the arm64 image derivation wired correctly and rely on arm64 runners for full arm builds.
- GitHub Actions image publication must run the `aarch64-linux` image leg on native arm64 infrastructure such as `ubuntu-24.04-arm`; Docker QEMU plus Nix `extra-platforms` on an x86 runner are not enough for the native arm64 Nix image build.
- `python3.11-websockets-15.0.1` is currently flaky on native `aarch64-linux` in nixpkgs `nixos-25.11`; keep its checks disabled in the shared router/dashboard Python override scope until upstream or nixpkgs lands a fix.
- `gws` and `bws` are the approved non-`ghostship-*` extra CLIs in the default image; keep `gws` pinned through the upstream flake package, keep `bws` sourced from nixpkgs, and do not revive vendored or seeded Google Workspace skills.
- Keep `ghostship-hermes-image` as the explicit publishable image bundle contract for CI, GHCR pushes, and image-loading flows, and keep the lower-level `/init` workstation tarball on a separate `ghostship-hermes-rootfs` output so scripts do not guess artifact semantics from one overloaded path.
- Git worktrees do not carry ignored local `.envrc` files by default. Live-test helpers should check the current worktree first, then another repo worktree with `.envrc`.
- `apply_patch` is currently unreliable for files inside git worktrees in this repo. When editing worktree files, prefer direct non-interactive scripted edits (for example Python or `perl -0pi`) and verify the result immediately.
- Cloudflare Access service-token headers are test-only. Use `GHOSTSHIP_TEST_CF_ACCESS_CLIENT_ID` and `GHOSTSHIP_TEST_CF_ACCESS_CLIENT_SECRET` in utilities, and derive them from local `.envrc` values in the live-test harness.

### Service And API Integration

- Keep local topology such as service URLs, hostnames, ports, profile names, and workspace paths in env/config by default unless the value itself contains credential material.
- Standalone `ghostship-hermes-router` runs should default state under `${XDG_STATE_HOME:-~/.local/state}/ghostship-hermes/router`; only the Hermes image runtime should override that path to `/home/hermes/.local/state/ghostship-hermes/router`.
- The local router should accept Hermes API-server env aliases (`API_SERVER_HOST`, `API_SERVER_PORT`, `API_SERVER_KEY`, `API_SERVER_CORS_ORIGINS`) alongside repo-specific `GHOSTSHIP_ROUTER_*` names so image wiring and standalone runs can share one config contract.
- The current public router alias set is `auxiliary`, `coding`, `agentic`, `vision`, and `tts`; Hermes root plus both managed profiles should default to `coding`, while `auxiliary` remains an extra alias rather than the default runtime lane.
- When provider metadata exposes capabilities, require tool calling only for `auxiliary` and `coding`; allow free `vision` models with image or video input plus text output, and allow free `tts` models only when they provide speech-style audio output rather than music generation.
- The local router may inventory paid models for debug/state visibility, but route selection and failover must remain free-only.
- Router startup should reuse the last persisted inventory and rankings when available; if no persisted inventory exists yet, keep routing unavailable until the background discovery pass completes instead of forcing a foreground refresh.
- Dynamic alias discovery should stay free-only, prefer an OpenCode Zen worker for startup bucketing when available, fall back to OpenRouter only when Zen cannot supply a usable worker, require tool-calling-capable text-output models only for `auxiliary` and `coding`, allow `vision` models with image or video input plus text output, and allow `tts` models only for speech-style audio output while excluding music-generation models such as Lyria.
- Zen inventory is sparse on native metadata; when a Zen model confidently matches a public OpenRouter model id after normalization, reuse OpenRouter description, created, and modality/tool metadata for Zen scoring and capability checks.
- Alias-specific family ordering should bias `coding`, `agentic`, and `auxiliary` after capability and free-only filters by applying relative rank bonuses only to families that are actually present, recency bias should be strong enough to lift newer families instead of acting only as a weak tie-breaker, exact id/name family matches must outrank description-only hints, `coding`/`agentic`/`vision` should use only a modest global size-rank bonus and should only penalize smaller variants when a larger sibling exists in the same family or inferred subfamily, and `auxiliary` should prefer smaller helper models.
- Router alias pins may still use repo-friendly `openrouter/` or `opencode/` prefixes, but backend dispatch must normalize those prefixes away so provider calls use the provider's real model id.
- Hermes router compatibility should be judged against the OpenAI-compatible backend API Hermes runtime calls directly, especially `responses.stream/create` and streamed `chat.completions` reasoning/tool-call deltas, not just the lighter Hermes gateway frontend surface.
- When Hermes talks to the local router through its generic OpenAI-compatible `model.base_url`, `OPENAI_API_KEY` is the compatibility auth input to reuse for the router bearer token.
- Upstream Hermes only treats `model.base_url` as the active custom endpoint during runtime resolution when `model.provider` is explicitly `auto` or `custom`; in this repo's router-primary image configs, always write `model.provider = auto` alongside the local router `base_url`.
- Router startup must not block the listener on fresh ranking generation; keep serving persisted inventory/rankings from SQLite while startup refresh and reranking continue in the background.
- Router score preview paths such as `/v1/models` must not reread full SQLite state tables for every candidate score; cache `model_state`, `provider_state`, `rankings`, and override reads in-process and invalidate those caches on writes.
- Root-side image validation shells only see the system profile PATH, so keep tools like `jq` in `environment.systemPackages` if the smoke or persistence scripts need them through `docker exec` as root.
- `docs/api/` follows a hybrid rule: every `ghostship-*` utility needs a canonical Markdown API reference, and services with upstream machine-readable specs should also keep the mirrored raw JSON artifact beside it.
- `ghostship-chaptarr` requires `CHAPTARR_URL`, `CHAPTARR_API_KEY`, and optional `CHAPTARR_API_PATH`/`CHAPTARR_API_VERSION`; document those env vars alongside the OpenAPI mirror so operators know how to configure the runtime.
- RomM v4.7.0 auth uses `POST /api/token` with the OAuth password grant (`username`, `password`, `grant_type=password`), not a static token flow.
- CloakBrowser Manager auth uses the server `AUTH_TOKEN` as `Authorization: Bearer <token>`; `/api/status` stays unauthenticated for health checks.
- `ghostship-cloakbrowser` previously built URLs without the slash before `api`; valid credentials still failed until that was fixed.
- qBittorrent WebUI automation uses cookie auth at `/api/v2/auth/login`, not a static API key.
- NZBGet automation uses JSON-RPC over `/jsonrpc` with HTTP Basic auth, not a REST resource model.
- Synology has official PDF docs for DSM login and File Station. DSM docs cover `enable_syno_token=yes`, `sid`, `synotoken`, and `SynoToken`; File Station docs cover the broader namespace inventory.
- Grimmory source-of-truth is the official `grimmory-tools/grimmory` repository. It is the BookLore successor; document its API from that repo’s controllers, not unrelated `grimoire` services.
- PriceBuddy exposes authenticated API docs at `/docs/api`, but the raw OpenAPI export is effectively token-gated. If no authenticated export is available, document the surface from upstream tests and handlers instead of inventing a spec mirror.
- RSS-Bridge is action-driven, not CRUD-driven. “Create a feed” means generating a canonical `action=display` URL from bridge schema, not persisting a server-side object.
- changedetection.io's stable upstream API source of truth is `docs/api-spec.yaml` in the official repo. Persist the repo mirror as `docs/api/changedetection-openapi.json`; treat `/api/v1/full-spec` as the live merged instance-specific extension surface.
- The deployed RSS-Bridge instance returns two parameter shapes: a dict of contexts or a legacy list of parameter groups that should be treated as the global context.
- OpenCode Zen `GET /models` currently returns only basic model cards, so router support for mixed Zen endpoint families must learn and cache the working family per model instead of expecting Zen inventory to declare it.

### Testing And Known Service Conditions

- The live integration suite should skip service-side read-only constraints instead of reporting them as client regressions.
- Current known skips and caveats:
  - RomM credentials only allow `heartbeat` and `config`.
  - Grimmory is more stable when a bearer token is cached once per session instead of re-authing every CLI call.
  - pyLoad may still return `401 Invalid API credentials` without valid API auth.
  - FlareSolverr may be absent from DNS.
  - Prowlarr search may time out on upstream indexer latency.

### Python Packaging

- Build the shared `ghostship-cli-contract` package from the same Python package set as each consuming CLI package. Mixing `python3` with `python311Packages` can pass local package tests and still fail `nix flake check` in GitHub.
