## Context

`ghostship-hermes` currently publishes a repo-owned dashboard stack:

- `packages/hermes-dashboard` builds a custom FastAPI backend plus React frontend
- `ghostship-hermes-hudui.service` starts that package on port `7681`
- the browser contract includes Ghostship-only APIs such as `/api/health`, `/api/profiles`, `/api/projects`, and `/api/console`
- the browser contract also owns a same-origin `ttyd` proxy and `Console` tab

Upstream Hermes `v0.9.0` now ships its own local dashboard with native pages and APIs for status, config, env, sessions, logs, analytics, cron, and skills. Continuing to carry the custom dashboard means the repo has two browser-management surfaces for the same Hermes runtime, plus custom tests, docs, and AGENTS memory that all drift away from upstream.

This change crosses packaging, systemd startup, image health checks, smoke tests, docs, OpenSpec contracts, and the repo’s image split assumptions. It is also intentionally breaking for browser-terminal behavior: the repo will stop treating browser terminal launch as part of the supported dashboard contract.

The user also requires that the native dashboard remain embeddable and usable inside a cross-origin iframe on the deployed host. That means upstream alignment cannot stop at “page loads directly”; the final runtime must also avoid frame-deny behavior and must prove the native UI still functions when loaded as embedded content.

## Goals / Non-Goals

**Goals:**

- Replace the repo-owned dashboard with the upstream Hermes native dashboard from the pinned Hermes release.
- Adopt the upstream Hermes dashboard port contract `9119` instead of preserving the repo’s custom `7681` browser port.
- Preserve the managed single-agent runtime, persisted `/home/hermes`, router service, and CLI/debug workflows.
- Preserve or add the browser/header/runtime behavior needed for cross-origin iframe embedding of the native dashboard.
- Remove the custom browser-only `ttyd`/`Console` contract instead of carrying it forward behind a compatibility layer.
- Align packaging, tests, docs, changelog, AGENTS memory, and OpenSpec requirements to the native dashboard.

**Non-Goals:**

- Rebuild the upstream dashboard to mimic the old MMX/HUDUI layout.
- Add a new Ghostship browser shim that reintroduces custom APIs or custom router/dashboard overlays.
- Preserve `/api/health`, `/api/profiles`, `/api/projects`, `/api/console`, browser terminals, or the `/workspace` Projects panel as compatibility contracts.
- Turn the Hermes native dashboard into a Ghostship router administration UI.

## Decisions

### 1. Serve the upstream Hermes dashboard directly on port `9119`

The managed image will publish the upstream Hermes dashboard on its native default port `9119` rather than preserving the repo-owned `7681` browser port.

Why:

- fully adopts the upstream dashboard contract instead of keeping a repo-local port convention
- avoids keeping a Ghostship reverse-proxy/controller layer alive only to forward from `7681` to `9119`
- makes the browser surface materially upstream-owned instead of “upstream app behind a custom shell”

Alternatives considered:

- Run upstream on `9119` and keep a Ghostship web shim on `7681`. Rejected because it preserves a repo-owned browser layer and leaves the repo maintaining custom HTTP behavior.
- Preserve `7681` by changing upstream’s bind port. Rejected because the user explicitly wants the upstream dashboard port and contract.

### 2. Remove the custom dashboard package and browser APIs entirely

`packages/hermes-dashboard` and its custom FastAPI/API/frontend/test surface should be retired rather than kept as a compatibility facade.

Why:

- user request is to replace custom dashboard completely
- dual browser contracts create permanent drift and duplicated maintenance
- custom dashboard APIs are tightly coupled to Ghostship-only concepts that upstream does not own

Alternatives considered:

- Keep a thin compatibility API for `/api/health` and friends. Rejected because it prolongs the old contract and keeps tests/docs split across two browser surfaces.

### 3. Drop browser-terminal ownership from the dashboard contract

The repo will stop treating browser terminal access as a first-class dashboard feature. Admin/debug shell workflows stay available through normal CLI/container access, not through a `Console` tab or same-origin `ttyd` proxy.

Why:

- upstream dashboard does not provide the repo’s `ttyd` browser contract
- re-injecting `ttyd` into the native dashboard would recreate a Ghostship-specific browser fork
- removing browser terminal ownership is the cleanest interpretation of “replace custom dashboard completely”

Alternatives considered:

- Add a custom tab or sidecar page that embeds `ttyd` next to the native dashboard. Rejected because it recreates the custom browser surface under a different name.

### 4. Make the Hermes runtime package the dashboard packaging source of truth

The image should launch whatever upstream Hermes package/wrapper provides for the native dashboard, including required Python extras and built web assets. Any repo packaging work should happen in the Hermes package/wrapper path, not in a separate Ghostship dashboard derivation.

Why:

- keeps dashboard code/assets aligned to the exact pinned Hermes release
- avoids a second build pipeline for frontend assets
- reduces custom packaging seams in the final image

Alternatives considered:

- Copy upstream frontend assets into a new repo package. Rejected because it recreates the drift problem in packaging form.

### 5. Rewrite validation around upstream dashboard pages and APIs on `9119`

Image health and smoke tests should validate that:

- the dashboard root loads on `9119`
- native Hermes dashboard APIs/pages needed for operator validation respond
- the dashboard can load and function when embedded from another origin via iframe on the deployed host
- managed config/env/session/gateway facts are inspectable through upstream surfaces

They should no longer assert custom `/api/health`, `/api/profiles`, `/api/projects`, `/api/console`, or `ttyd` websocket behavior.

Why:

- those checks prove the retiring implementation, not the target implementation
- replacement is incomplete if the image still depends on custom browser APIs to pass

### 6. Update image-split assumptions to treat the dashboard as upstream Hermes content

OpenSpec and docs currently treat `hermes-dashboard` as a repo-owned final-layer package. After this change, the browser surface should be described as part of the upstream Hermes runtime/toolchain, while Ghostship final-layer ownership remains on router/runtime/utilities and managed service wiring.

Why:

- matches the actual ownership boundary after replacement
- prevents future specs/docs from resurrecting `packages/hermes-dashboard` as a required final-image artifact

## Risks / Trade-offs

- [Risk] Upstream docs and source disagree on command naming (`hermes web` vs `hermes dashboard`). → Mitigation: verify the pinned release’s actual CLI entrypoint and wrap that exact command in systemd/tests.
- [Risk] Current Nix packaging for `hermes-agent-wrapped` may not include the upstream web extras or built assets needed to launch the dashboard. → Mitigation: teach the wrapped Hermes package path to include web dependencies/assets and validate launch in-image.
- [Risk] Operators lose browser shell access they currently use through the `Console` tab. → Mitigation: call out the removal explicitly in proposal/docs/changelog and keep CLI/admin workflows available.
- [Risk] Existing smoke tests, health checks, and docs are deeply anchored to the retiring custom APIs. → Mitigation: rewrite all browser validation and documentation as part of the same change instead of leaving partial compatibility.
- [Risk] Moving the published browser port from `7681` to `9119` breaks compose files, deploy manifests, port-forward rules, firewall assumptions, and smoke tests that encode the old port. → Mitigation: update all docs/tests/specs in the same change and mark the port shift as breaking.
- [Risk] Binding the native dashboard on `9119` may widen exposure relative to upstream localhost defaults if the image continues to publish it broadly. → Mitigation: keep the repo’s explicit image/network posture documented and preserve cautionary docs around public exposure.
- [Risk] Upstream dashboard security headers or middleware could prevent cross-origin iframe embedding even when the direct page works. → Mitigation: inspect response headers in-image and on `chill-penguin`, then patch runtime/header behavior only as much as needed to preserve upstream UI while allowing the required iframe embed path.

## Migration Plan

1. Verify the exact upstream dashboard command and package requirements for the pinned Hermes release.
2. Rewire the image/service startup so port `9119` serves the upstream Hermes dashboard directly.
3. Remove the repo-owned dashboard package and all related service/runtime/test references.
4. Rewrite image health checks and smoke tests against the upstream dashboard contract.
5. Add live validation that proves the dashboard can be embedded cross-origin and remains functional on `chill-penguin`.
6. Update README, CHANGELOG, AGENTS durable lessons, and OpenSpec specs/tasks so the old browser contract is gone everywhere.
7. Roll out on a test image first; if the native dashboard packaging, header behavior, or runtime wiring proves incomplete, rollback is to restore the repo-owned dashboard service and package until the upstream path is made launchable in-image.

## Open Questions

- Which exact command should the service own for the pinned Hermes release: `hermes dashboard` or `hermes web`?
- Does the pinned Hermes package already include built dashboard assets in the wrapped Nix output, or must the repo extend the wrapper/package to include `hermes-agent[web]` support?
- Should image validation use only native REST APIs, or should it also include browser-driven checks for critical pages such as status/config/env/sessions?
- Should the image continue publishing `9119` externally by default, or should deploy docs recommend proxy-only exposure even though the runtime itself uses the upstream port?
- If upstream sets restrictive frame headers in a later release, should the repo patch the Hermes web server directly or add a minimal response-header wrapper around the upstream dashboard process?
