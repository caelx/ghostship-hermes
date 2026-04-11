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
- Do not preinstall Codex, Opencode, OpenSpec, `skills`, or `feed` in the default image; `gws`, `gcloud`, `bws`, `gh`, and OpenSSH client tools are the approved extra CLIs, including SSH key generation through `ssh-keygen`.
- Keep the browser surface minimal: one dashboard, on-demand ephemeral `ttyd`, no persistent per-profile terminal services.
- Keep the image on one repo-owned managed Hermes agent rooted at `/home/hermes/.hermes`; do not reintroduce a repo-owned named-profile fleet.
- Keep one persistent managed gateway service, `ghostship-hermes-gateway.service`, supervised by NixOS systemd units.
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
- Upstream Hermes profiles are still anchored to `~/.hermes/profiles/...`, but this image's supported runtime surface is the root managed agent under `/home/hermes/.hermes`; repo-owned named profiles are no longer part of the contract.
- A minimal declarative gateway config is enough to boot the Hermes service even before operator-specific provider or messaging settings are added.
- Hermes `doctor` only marks the `messaging` toolset available when `gateway.status` sees a live gateway via `gateway.pid`; projecting Discord env into the root managed `.env` is necessary to configure the gateway, but it is not sufficient to make the warning disappear if the gateway never starts or has already failed.
- The managed gateway service should own `/home/hermes/.hermes/gateway.pid` itself: write the full JSON liveness record for the current service PID before `exec`, remove stale pidfiles before start and after stop, and treat `gateway_state.json` as informational rather than the primary liveness contract.
- Hermes health/status validation must also recognize the wrapped managed gateway argv (`.hermes-wrapped gateway run --replace`); otherwise commands such as `hermes doctor` can decide the live service is invalid and delete `gateway.pid` even while `ghostship-hermes-gateway.service` is still active.
- Upstream Hermes does not expose this single-agent repo contract directly, so keep the repo-owned bootstrap, env rewrite, seed staging, and managed gateway service implemented as NixOS-managed units rather than mutable runtime drift.
- The browser dashboard now follows the HUDUI product shape, with `/workspace` wired in as the Projects root and one Ghostship-specific `Console` tab that spawns an on-demand `ttyd` session focused on `/workspace`.
- The dashboard proxies ttyd from its own origin on `:7681`; do not turn ttyd `--check-origin` back on for proxied sessions or tab switches will fall into ttyd's reconnect overlay.
- Keep `GHOSTSHIP_DASHBOARD_PORT=7681` and `GHOSTSHIP_TTYD_PORT_BASE=7682` in the managed service environment, not just the runtime wrapper, because the dashboard systemd unit starts `hermes-dashboard` directly and otherwise falls back to its package default port.
- The ttyd proxy must stream decoded HTTP bytes and preserve websocket subprotocol negotiation; stripping `content-encoding` while forwarding raw gzip bytes or accepting the browser websocket before upstream subprotocol negotiation will break the embedded terminal.
- HUDUI validation is an operator-facing surface: keep `/api/health`, `/api/profiles`, `/api/projects`, and `/api/console` aligned to the managed runtime contract so live image checks can verify the browser/runtime wiring without shelling into the container first.
- Keep the published image healthcheck on a store-stable `curl` path inside the image metadata; relying on `/run/current-system/sw/bin/curl` can race during cold boot and produce a false first failure.
- The image should bootstrap one managed agent rooted at `/home/hermes/.hermes`; repo-owned workflows should use root-scoped `hermes ...` commands instead of `hermes -p <profile>`.
- The bootstrap oneshot should preserve one root skill tree, seed `/home/hermes/.hermes/SOUL.md` from `/home/hermes/seeds/SOUL.md`, replace the old repo-owned profile fleet during migration, keep future seed updates in sync only while the live `SOUL.md` still matches the last seeded hash, and write the managed runtime env into `/home/hermes/.hermes/.env` without depending on extra Python packages like PyYAML.
- During single-agent migration, if `/home/hermes/.hermes/SOUL.md` exists without a seed marker and still matches the upstream unmanaged default Hermes prompt, bootstrap should replace it with the repo seed and create the marker; do not treat that legacy default as a user customization.
- Bootstrap should rewrite the managed root `.env` atomically because that path is watched by the managed gateway restart unit; rewriting the watched file in place can restart the gateway against a partially written `.env`.
- Keep `diffutils` in the managed service PATH: the bootstrap env writer uses `cmp` to avoid pointless `.env` rewrites, and dropping that binary turns a clean no-op comparison into a boot-time shell error.
- Keep `/etc/ghostship-hermes-release` as the immutable image-scoped version marker, and mirror it into `/home/hermes/.ghostship-hermes-release` on every boot so persisted home state reports the currently booted image version instead of the first version that created the volume.
- The managed gateway should treat `/home/hermes/.hermes/.env` as the single operator-facing source of truth via systemd `EnvironmentFile`; if the managed env contract changes, update the bootstrap writer rather than layering more service-level env overrides.
- The managed `.env` should hold only the agent-facing runtime contract: Hermes/provider secrets, browser config, Discord settings, webhook settings, Bitwarden access, and every utility/service env that installed `ghostship-*` CLIs or router-invoked utility calls need at runtime. Keep image infrastructure, router-daemon internals, container boot plumbing, and test-only utility headers outside the managed `.env`.
- Optional runtime skill staging lives under `/home/hermes/seeds/skills/<skill>`; bootstrap may copy a missing skill directory only into `/home/hermes/.hermes/skills/<skill>`, it must never overwrite an existing destination skill because Hermes owns it after first seed, and it should normalize the full managed skills tree to writable user-owned permissions after materializing Hermes built-ins.
- Upstream Hermes Nix `services.hermes-agent.settings` deep-merges across module definitions and preserves on-disk user-added keys that Nix does not touch; use Nix first for the scaffolded defaults, but let untouched runtime keys survive rebuilds.
- For Hermes auxiliary tasks, setting `base_url` bypasses provider resolution entirely; use a direct endpoint only when you do not want Hermes to keep walking its native auxiliary provider chain for that task.
- The current single-agent scaffold expects `model.provider = opencode-go` plus `model.default = minimax-m2.7` as the primary lane, a `fallback_model` that uses the local router alias `agentic` through `http://127.0.0.1:8788/v1` with `OPENAI_API_KEY` as the router bearer token, the managed router env default `GHOSTSHIP_ROUTER_DISABLED_MODELS=openrouter/free`, `OPENCODE_GO_API_KEY` for the direct MiniMax path, `GOOGLE_AI_STUDIO_API_KEY` for all direct auxiliary tasks, and `BWS_ACCESS_TOKEN` only for Bitwarden-backed workflow secrets.
- OpenCode Go does not expose the generic `/models` health path that Hermes `doctor` uses for several API-key providers; treat it like MiniMax for doctor validation and prove the direct path with an actual `https://opencode.ai/zen/go/v1/messages` request using `x-api-key`, not `Authorization: Bearer`.
- Hermes Codex OAuth should be initialized through root-scoped `hermes model` and stored in `/home/hermes/.hermes/auth.json`; do not assume `OPENAI_API_KEY` is part of the primary Codex path.
- Bootstrap should run `hermes skills list` under the Hermes runtime user so the skills hub directories and lockfile exist before validation, rather than depending on a manual first-run command.
- The scaffold enables Hermes `memory.provider = holographic` for the managed agent, with plugin settings under `plugins.hermes-memory-store`; this is local SQLite memory and does not need an extra API key.
- The scaffolded root `config.yaml` includes Discord defaults (`require_mention = true`, `auto_thread = false`, `reactions = true`, `group_sessions_per_user = true`), while bootstrap projects the generic single-agent Discord env contract directly into `/home/hermes/.hermes/.env`. Hermes still has no native Discord icon setting; distinct icons require distinct Discord bot applications outside Hermes.
- Tirith is intentionally installed in the image runtime and kept on the service PATH so Hermes pre-exec scanning can use `tirith_path = "tirith"` without a bootstrap download. The image also vendors `agent-browser` without preinstalling Chrome or Chromium; the shared scaffold sets `browser.cloud_provider = "local"` so Hermes local browser mode defaults to that CLI unless an operator manually attaches CDP with `/browser connect`. The managed single-agent runtime treats remote browser CDP as one operator-facing setting, `BROWSER_CDP_URL`.
- `ghostship-hermes-router` should reuse Hermes-facing provider env names where a matching backend exists; today that specifically means accepting `OPENCODE_GO_API_KEY` as an alias for the router's OpenCode Zen credential path, while `GOOGLE_AI_STUDIO_API_KEY` remains Hermes-direct until the router grows a native Google provider.

### Container And Supervisor Behavior

- The runtime needs a root init phase to prepare `/home/hermes`, `/home/hermes/.hermes`, `/workspace`, and `/nix` before dropping to the `hermes` user.
- Mounting an empty Docker volume over `/nix` on a fresh Nix-built image is unsafe: it can hide or copy the image store and stall `docker run`.
- Imported NixOS images may not expose `bash` through `docker exec bash`; image tests should use `/bin/sh` plus an explicit PATH to the NixOS system profile.
- The docker-container NixOS profile leaves the firewall active inside the container; published dashboard traffic requires explicitly allowing TCP `7681`.
- Persisted `/nix` must include a writable `/nix/var/nix/daemon-socket` path and the image must start `nix-daemon.socket` after storage preparation, or user-level `nix profile install` will fail even though `nix` is installed.
- Persisting `/home/hermes` directly is the supported durability model for this image; it keeps Hermes CLI profiles, managed state, XDG state, and later-installed agent-tool config together in one mount.
- Do not require the deployment host to expose port `7681` directly. Validate the dashboard from inside the Hermes container or through the intended upstream proxy path, and treat missing host-level `127.0.0.1:7681` reachability as expected unless the deployment specifically documents a direct bind.

### Skill Authoring

- Repo-managed service skills should stay short, trigger-rich, and workflow-oriented: prioritize start-here guidance plus inspect -> dry-run -> mutate -> verify sequences over command dumps.
- Use family-level structure for service wrappers, but keep domain-specific ordering and failure guidance inside each skill instead of mass-applying identical wording.

### Platform And CI

- Scheduled GitHub release polling must authenticate with `GITHUB_TOKEN` or `GH_TOKEN`; anonymous `api.github.com` release queries can hit rate limits and break Actions.
- The Hermes release updater must change both `packages/hermes-image/hermes-release.txt` and the `hermes-agent` flake input/lock; updating only the label file does not change the packaged Hermes build.
- GitHub Actions pushes made with `GITHUB_TOKEN` do not trigger the repo's `push` workflows. If the Hermes release updater commits directly to `main`, it must explicitly dispatch `publish-image.yml` or use a different credential model.
- `ghostship-hermes-base` is now a true Hermes/core-runtime layer: keep repo command surfaces out of the base closure, point any base-side runtime handoff at `/opt/ghostship-overlay/bin`, and let the overlay bundle omit store paths that are already present in the base closure.
- Dependency-audit rule for the image split: if the realized overlay still carries shared non-Ghostship closures used by the runtime or approved utility set, move those closures into the base image until the overlay store paths are limited to Ghostship-owned packages plus the small overlay assembly env. The approved base-side Python runtime closure now includes `ghostship-cli-contract`, `httpx`, `typer`, `fastapi`, `uvicorn`, `websockets`, `pydantic`, `pydantic-core`, `starlette`, `click`, `shellingham`, `annotated-types`, `typing-extensions`, `typing-inspection`, `python-dotenv`, `python-multipart`, `watchfiles`, `urllib3`, `yarl`, `anyio`, `httpcore`, `certifi`, `charset-normalizer`, `idna`, `sniffio`, `aiohttp`, `aiohappyeyeballs`, `aiosignal`, `attrs`, `frozenlist`, `multidict`, and `propcache` from the repo's overridden Python package set, plus the stable external utility closures (`agent-browser`, `bws`, `gcloud`, `gws`).
- The split-image boundary is only valid for the standalone base artifact and internal closure audit. Final `ghostship-hermes` publication must come from the explicit final image bundle, because systemd units, bootstrap wiring, and other managed runtime state are part of the final NixOS system closure rather than the lightweight overlay env.
- Hermes `v2026.4.8` expects a `system.activationScripts.setupSecrets` phase in its NixOS module ordering. This repo does not use a separate secrets activation module, so keep a no-op `setupSecrets` compatibility hook in the image module unless the module stack grows a real provider for it.
- The `hermes` user tooling refresh path must upgrade Hermes from an unlocked flake ref such as `github:caelx/ghostship-hermes#hermes-agent-wrapped`; a baked store path can bootstrap the first boot, but `nix profile upgrade --all` cannot move a locked store-path install forward.
- The image-managed `hermes` toolchain now lives in its own Nix profile at `/home/hermes/.local/state/nix/profiles/ghostship-managed`; keep that separation so boot-time convergence does not collide with operator-owned `~/.nix-profile` entries such as older `hermes-agent` installs.
- Repo-owned persisted user-layer system state must converge on boot and image replacement, not just accumulate: remove stale managed Nix-profile entries, reapply the declared managed npm project and `.local/bin` links, and use the current image generation as the source of truth for repo-managed runtime tooling and config.
- `ghostship-hermes-startup.service` must not require the mutable user-tooling oneshot for the main runtime to come up; bootstrap and the dashboard/router/managed gateway should keep booting even if tool refresh work fails.
- Hermes is not packaged in the inspected `nixos-25.11` nixpkgs tree, while `ttyd`, `codex`, and `opencode` are.
- Local flake evaluation only sees git-tracked files. Stage new Nix files and vendored trees before relying on `nix flake check` or `nix build` in a worktree.
- On this host, run only one Nix build or eval at a time; overlapping Nix client commands can wedge daemon responsiveness and create misleading validation failures.
- Keep `.nix-local-store/` gitignored. It is repo-local build state for Docker and Nix validation, not source content.
- On the current `x86_64` dev host, `nix flake check` does not build `aarch64-linux` outputs. Use `nix eval` locally to keep the arm64 image derivation wired correctly and rely on arm64 runners for full arm builds.
- GitHub Actions image publication must run the `aarch64-linux` image leg on native arm64 infrastructure such as `ubuntu-24.04-arm`; Docker QEMU plus Nix `extra-platforms` on an x86 runner are not enough for the native arm64 Nix image build.
- `python3.11-websockets-15.0.1` is currently flaky on native `aarch64-linux` in nixpkgs `nixos-25.11`; keep its checks disabled in the shared router/dashboard Python override scope until upstream or nixpkgs lands a fix.
- `gws`, `gcloud`, `bws`, `gh`, and the OpenSSH client tools are the approved non-`ghostship-*` extra CLIs in the default image; keep `gws` pinned through the upstream flake package, keep `gcloud`, `bws`, `gh`, and OpenSSH sourced from nixpkgs, rely on that OpenSSH package for `ssh`, `scp`, and `ssh-keygen`, and do not revive vendored or seeded Google Workspace skills.
- Keep `ghostship-hermes-image` as the explicit final-image contract for local export, image loading, and GHCR publication; the separate `ghostship-hermes-base` image may still be reused as a standalone artifact, but do not publish `ghostship-hermes` by reconstructing from `ghostship-hermes-overlay-bundle` because the managed runtime/systemd contract lives in the final NixOS image.
- GitHub publication should always rebuild the explicit `ghostship-hermes-image` bundle on the runner host. The supported acceleration path is the signed shared Nix binary cache in `caelx/ghostship-cache` via a runner-local `nixcache-oci` proxy; bootstrap failure may fall back to the uncached host-side build, but trust/signature mismatches must fail the build and the workflow must not disable signature verification.
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
- Keep the image split on one shared overridden Python package set for the base-side runtime closure, `ghostship-cli-contract`, `hermes-dashboard`, `ghostship-hermes-router`, and every `ghostship-*` Python utility; if those drift onto different package sets, GitHub content publishes will rebuild duplicate dependency closures even when the Docker base image is reused.
- For the managed Hermes user toolchain, install Python as one `python3.withPackages (ps: [ ps.pip ])` environment rather than separate `python3` and `pip` entries; separate packages can expose `pip` while still leaving `python3 -m pip` broken.
- In the managed `/home/hermes/.local/state/nix/profiles/ghostship-managed` profile, the pip-capable Python env and `hermes-agent-wrapped` both export `bin/python`; keep the Python env at a higher `nix profile` priority rather than expecting stale-entry removal alone to prevent file collisions.
