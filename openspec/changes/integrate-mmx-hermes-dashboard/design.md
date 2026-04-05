## Context

The repo already contains a new dashboard implementation in `packages/hermes-dashboard`: a Python package with a `hermes-dashboard` entrypoint, bundled static assets, and a FastAPI controller that serves the MMX UI and proxies on-demand `ttyd` sessions. The Hermes image path already partially consumes it through the NixOS module and the runtime wrapper, but the integration is incomplete:

- the runtime still exports a stale `GHOSTSHIP_DASHBOARD_ROOT` that points at a deleted legacy asset tree
- the flake uses the dashboard package internally but does not make the packaged dashboard path explicit enough for maintainers who want to build or inspect it directly
- the smoke test and docs still assert the older dashboard UI strings instead of the MMX UI contract
- the packaged dashboard contract is not captured in a current OpenSpec capability even though it is now the intended browser surface

This change crosses the dashboard package, Nix packaging, image runtime wiring, tests, and docs, so a design is useful before implementation.

## Goals / Non-Goals

**Goals:**
- Make `packages/hermes-dashboard` the only canonical dashboard implementation for the Hermes image.
- Ensure the image installs and runs the packaged `hermes-dashboard` binary under systemd.
- Keep the MMX UI and current FastAPI/`ttyd` behavior as the supported browser contract.
- Remove dead legacy seams that reference the deleted old dashboard asset path.
- Align smoke tests and docs with the MMX dashboard contract.

**Non-Goals:**
- Revert the UI to the older copy, markup, or visual treatment.
- Introduce a different dashboard architecture, framework, or service manager.
- Reintroduce persistent per-profile browser terminal services or a profile reconciler loop.
- Expand the dashboard into a broader control plane beyond the minimal MMX browser surface and terminal launcher.

## Decisions

### Keep the dashboard package self-contained

The canonical dashboard remains `packages/hermes-dashboard`, with static HTML/CSS/JS assets bundled in the Python package and served directly by the FastAPI app.

Why:
- the current app already resolves assets from its own package tree instead of a repo-local runtime path
- this is the least ambiguous packaging model for container installs
- it removes dependency on mutable repo checkout paths inside the image

Alternatives considered:
- Keep a separate image-local dashboard asset directory. Rejected because that recreates the stale split that already exists in the runtime wrapper.
- Serve assets from an external build artifact outside the Python package. Rejected because it adds another packaging surface without solving a current problem.

### Make the image runtime point only at the packaged dashboard

The systemd dashboard service should continue to execute `ghostship-hermes-runtime dashboard-controller`, and that wrapper should in turn execute the packaged `hermes-dashboard` binary with only the environment variables the package actually uses.

Why:
- the service graph and non-root runtime model are already correct
- the broken seam is the legacy dashboard-root export, not the systemd ownership model
- keeping the wrapper preserves the current storage preparation and environment-default flow

Alternatives considered:
- Exec the package binary directly from the NixOS unit without the runtime wrapper. Rejected because the wrapper still owns useful shared runtime defaults.
- Add another custom launcher just for the dashboard. Rejected because it duplicates logic already present in `ghostship-hermes-runtime`.

### Treat the MMX UI contract as the test and documentation source of truth

Image tests and docs should validate the MMX dashboard’s real entrypoint markers and runtime behavior rather than older UI copy such as `Open Terminal` and `Two declared Hermes profiles`.

Why:
- current tests are asserting a contract that the canonical frontend no longer implements
- the user explicitly chose the MMX UI as canonical
- tests should validate stable user-visible behavior and service readiness, not stale strings from a replaced interface

Alternatives considered:
- Change the MMX UI back to satisfy old tests. Rejected because that would reverse the canonical product decision.
- Keep old string assertions alongside new behavior assertions. Rejected because it preserves conflicting contracts.

### Expose a clearer packaged-dashboard build path

The flake should make the dashboard package easy to build and inspect as a first-class package output in addition to consuming it inside the image graph.

Why:
- maintainers want the package “built and installed” as a real artifact, not just hidden inside the NixOS image closure
- a direct package output reduces ambiguity during debugging and validation

Alternatives considered:
- Rely only on the image build to prove the dashboard package exists. Rejected because it makes isolated package verification harder than necessary.

## Risks / Trade-offs

- [Python package omits static assets] → Ensure the package build explicitly ships `static/` content so the container does not serve a backend without a frontend.
- [Tests become too copy-specific again] → Update smoke tests to check MMX-visible markers plus runtime behavior rather than fragile remnants of previous UI text.
- [Legacy env cleanup removes a still-needed seam] → Remove only the deleted asset-path variable and keep the runtime defaults that the FastAPI app still consumes.
- [Spec drift remains in adjacent runtime capabilities] → Limit this change to the dashboard package contract and the runtime requirement that directly references the dashboard service path.

## Migration Plan

1. Update the dashboard package/Nix packaging path so the built artifact clearly includes the MMX frontend assets and exposes a direct buildable package output.
2. Remove the stale legacy dashboard-root runtime seam while keeping the current systemd service shape.
3. Update image tests and docs to the MMX dashboard contract.
4. Rebuild the image and run the dashboard smoke test against the packaged dashboard path.
5. If verification fails, roll back by restoring the previous branch state; no persistent data migration is required because this change targets packaging, service wiring, and tests rather than stored user state.

## Open Questions

- Whether the smoke test should assert one or more explicit MMX UI markers in addition to behavior checks, or prefer behavior-first assertions with only a minimal MMX sentinel.
