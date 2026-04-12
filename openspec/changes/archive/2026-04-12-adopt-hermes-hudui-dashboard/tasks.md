## 1. Package HUDUI As The Canonical Dashboard

- [x] 1.1 Replace the current `packages/hermes-dashboard` implementation with a HUDUI-derived backend/frontend package layout and add the frontend build steps needed to ship compiled HUDUI assets in the package artifact.
- [x] 1.2 Update `flake.nix` and image package wiring so the HUDUI-derived dashboard artifact is the canonical browser package consumed by the image build.
- [x] 1.3 Add a new HUDUI-specific managed browser service on port `7681` and remove the old `ghostship-dashboard-controller.service` startup wiring from the image runtime.

## 2. Adapt HUDUI To The Ghostship Image Layout

- [x] 2.1 Wire the HUDUI runtime environment to the managed single-agent layout at `/home/hermes/.hermes`.
- [x] 2.2 Define and wire the HUDUI projects-directory contract to `/workspace` so the Projects panel reflects the image's persisted work-products mount.
- [x] 2.3 Patch HUDUI collectors and frontend assumptions so the browser surface works cleanly in the single-agent image layout without depending on the removed Ghostship `/api/status` contract.
- [x] 2.4 Integrate the dashboard's managed-gateway display and health hooks with the separate gateway-alignment change without reimplementing that gateway migration here.

## 3. Add The Ghostship Console Extension

- [x] 3.1 Add a top-level `Console` tab to the HUDUI frontend and route it through the normal HUDUI browser navigation.
- [x] 3.2 Implement the backend terminal lifecycle and same-origin `ttyd` proxy support that the Console tab needs.
- [x] 3.3 Verify the Console tab shows a usable loading state, attaches to a live terminal session, and tears down the backing `ttyd` process when the session is closed.

## 4. Validate, Document, And Prove The Migration

- [x] 4.1 Update the dashboard smoke and persistence tests to validate HUDUI endpoints, HUDUI browser behavior, and the Console workflow instead of the old MMX markers and `/api/status` API.
- [x] 4.2 Update `README.md`, `AGENTS.md`, `CHANGELOG.md`, and related runtime/OpenSpec references so HUDUI is documented as the canonical browser surface.
- [x] 4.3 Build the HUDUI-derived dashboard package and the Hermes image locally and run the updated dashboard validation flow.
- [x] 4.4 Deploy the rebuilt image to `chill-penguin-root2` over `ssh`, create a tunnel from the remote dashboard port to a local browserable port, and verify the HUDUI browser service loads through that tunnel.
- [x] 4.5 Verify through the `chill-penguin-root2` tunnel that the HUDUI Projects panel reflects `/workspace` and the Console tab can open a live same-origin `ttyd` session.
