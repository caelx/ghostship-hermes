## Context

The repo currently ships a bespoke dashboard in `packages/hermes-dashboard`: a FastAPI app with bundled static assets, a repo-specific `/api/status` contract, and built-in `ttyd` session management. The image wires that package into `ghostship-dashboard-controller.service`, and the smoke/persistence tests assert the Ghostship-specific browser markers and terminal API.

`hermes-hudui` has a different product and technical contract. It expects a FastAPI backend that serves HUDUI-specific `/api/*` endpoints, a `/ws` update channel, a React/Vite frontend build, and data collection directly from the Hermes state directory. It also expects a projects directory contract that is separate from the Hermes state directory. That is close enough to the image's current `/home/hermes/.hermes` plus `/workspace` layout to make adoption feasible, but not close enough for a drop-in swap.

This design intentionally excludes the upstream-aligned managed gateway-service migration. A separate change will establish the final gateway service contract. This HUDUI migration must consume that contract without redefining it.

## Goals / Non-Goals

**Goals:**
- Make `hermes-hudui` the canonical browser product shipped by the image.
- Replace the old Ghostship dashboard service and API contract with a HUDUI-aligned managed browser service on the published dashboard port.
- Keep the single-agent Ghostship image layout (`HERMES_HOME=/home/hermes/.hermes`, persisted `/home/hermes`, persisted `/workspace`) while making it legible to HUDUI.
- Add one Ghostship-specific HUDUI extension: a `Console` tab backed by on-demand same-origin `ttyd`.
- Update tests, docs, and OpenSpec so they describe HUDUI plus the console tab rather than the old minimal dashboard.

**Non-Goals:**
- Preserve compatibility with the old `/api/status` contract, old HTML markers, or old browser-copy expectations.
- Keep `ghostship-dashboard-controller.service` alive as a compatibility shim.
- Redesign HUDUI into a new product shape that diverges from upstream beyond the `Console` extension and image-compatibility glue.
- Define the upstream-aligned gateway-service migration itself.

## Decisions

### Adopt HUDUI as the canonical package source inside `packages/hermes-dashboard`

`packages/hermes-dashboard` should stop modeling the old Ghostship dashboard implementation and instead become the repo's packaged HUDUI distribution point, with the Ghostship console extension and image-specific compatibility patches living there.

Why:
- The repo already treats `packages/hermes-dashboard` as the canonical browser artifact.
- Reusing that package path minimizes image/flake churn while still replacing the product contract.
- Keeping the HUDUI-derived code local to the package gives the repo a stable place to patch the console tab and image-specific compatibility behavior.

Alternatives considered:
- Add a second package such as `packages/hermes-hudui` and keep `packages/hermes-dashboard` around temporarily. Rejected because it preserves two competing browser artifacts and delays the contract cutover.
- Treat HUDUI as an external runtime checkout. Rejected because the image build must remain reproducible and self-contained.

### Build the HUDUI frontend in Nix as part of the package artifact

The packaged dashboard artifact should gain a real frontend build phase that compiles the HUDUI React/Vite frontend and installs the resulting static assets beside the Python backend.

Why:
- HUDUI expects a Node/Vite build, not precommitted static files alone.
- The image needs a deterministic package artifact that can be built in CI and included in the Nix closure.
- The current Python-only package shape does not satisfy HUDUI's asset contract.

Alternatives considered:
- Prebuild HUDUI assets outside Nix and commit the built bundles. Rejected because that adds drift-prone generated artifacts to source control.
- Serve the frontend from a separate runtime service. Rejected because it complicates the browser contract without solving a repo need.

### Replace the current dashboard unit with a HUDUI-specific managed browser service

The image should stop starting `ghostship-dashboard-controller.service` and instead run a new HUDUI-specific systemd unit as the canonical browser service on port `7681`.

Why:
- The old unit name and behavior encode the old dashboard contract.
- The user explicitly asked not to keep the old systemd service.
- A clean service replacement makes the runtime and validation contracts less ambiguous.

Alternatives considered:
- Keep the old unit name and only change the command. Rejected because it preserves stale operational semantics.
- Add a wrapper unit that starts the old and new service shapes. Rejected because it creates an unnecessary migration shim in the long-lived contract.

### Treat the Ghostship console feature as a thin HUDUI extension

The only intentional Ghostship-specific feature should be a new top-level `Console` tab in HUDUI. That tab should own the on-demand `ttyd` lifecycle and same-origin proxying that the current dashboard already provides.

Why:
- The user wants to align with HUDUI, not fork it into a new dashboard product.
- A single dedicated tab is the smallest extension that preserves browser-terminal workflows.
- Keeping terminal orchestration in the HUDUI backend preserves the current same-origin and websocket behavior that works well in the image.

Alternatives considered:
- Keep the old Ghostship left-rail terminal UI inside HUDUI. Rejected because it preserves too much of the old dashboard product.
- Run `ttyd` as separate long-lived services outside HUDUI. Rejected because the repo explicitly prefers on-demand ephemeral terminals.

### Define `/workspace` as the HUDUI projects root for the image

The image should explicitly set the HUDUI projects-directory contract to `/workspace` rather than relying on HUDUI's default `~/projects`.

Why:
- `/workspace` is already the repo's persisted work-products mount.
- HUDUI expects a projects root separate from `HERMES_HOME`.
- Making the projects root explicit avoids an accidental contract where the Projects panel is empty or points at the wrong directory.

Alternatives considered:
- Create or recommend `~/projects` inside `/home/hermes`. Rejected because it would introduce a second competing work-products convention.
- Disable the Projects panel in the image. Rejected because that would move away from true HUDUI alignment.

### Keep the dashboard compatibility layer generic about the managed gateway contract

HUDUI integration should not define the gateway rename itself. Instead, the dashboard/backend compatibility code should consume the managed gateway contract that the separate gateway-alignment change establishes.

Why:
- The user explicitly split the gateway work into another change.
- Duplicating that work here would create conflicting ownership.
- The dashboard still needs a way to display managed-gateway state, but that can be wired through whichever service/path conventions the other change finalizes.

Alternatives considered:
- Hard-code the current Ghostship gateway unit into the HUDUI migration. Rejected because it would immediately conflict with the other change.
- Block the HUDUI migration until the gateway change is fully merged. Rejected because the browser migration can still be proposed and implemented against an abstracted managed-gateway contract.

## Risks / Trade-offs

- [HUDUI adoption reintroduces profile-centric UI assumptions] -> Patch the backend/frontend so the root managed agent renders cleanly in HUDUI while still exposing HUDUI's broader product shape.
- [The frontend build adds Nix/Node packaging complexity] -> Keep the package boundary narrow: one Python backend artifact plus one deterministic frontend build output.
- [Console integration drifts too far from upstream HUDUI] -> Constrain the extension to one top-level tab plus backend routes needed for `ttyd`.
- [Projects panel does not update live when rooted at `/workspace`] -> Wire the projects root explicitly and extend the watcher/runtime integration to monitor the configured projects path rather than only HUDUI defaults.
- [The separate gateway-alignment change lands different service details than expected] -> Keep this design generic about gateway naming and consume the managed-gateway contract through a narrow compatibility seam.

## Migration Plan

1. Replace the old dashboard package contents with a HUDUI-derived package layout that includes the frontend build.
2. Add the Ghostship `Console` tab and the backend `ttyd` lifecycle/proxy support needed by that tab.
3. Replace the old dashboard systemd unit with a new HUDUI-specific managed browser service on port `7681`.
4. Wire HUDUI's runtime environment for the image, including `HERMES_HOME=/home/hermes/.hermes` and a HUDUI projects root of `/workspace`.
5. Update smoke and persistence validation to assert the HUDUI contract and console behavior instead of the old Ghostship markers and APIs.
6. Build the packaged dashboard and image artifacts and verify the new browser contract locally.
7. Deploy the rebuilt image to `chill-penguin-root2` over `ssh`, create a local tunnel to the remote dashboard port, and verify the HUDUI surface, console workflow, and persisted-state behavior through that browseable tunnel.
8. Update README/OpenSpec/runtime docs to describe HUDUI as the canonical browser surface.
9. Roll back, if needed, by restoring the previous dashboard package and browser-service wiring; no user-state migration is required because persisted Hermes state and `/workspace` remain in place.

## Open Questions

- Whether the repo should preserve the `hermes-dashboard` package/output name as a HUDUI-derived compatibility alias or rename the package artifact itself to match HUDUI more directly.
- Whether the console tab should manage a single live terminal session at a time or preserve the current multi-session behavior behind one HUDUI tab.
