## Why

The current `ghostship-hermes` browser surface is a repo-specific minimal dashboard with a custom API, custom service, and custom validation contract. The user wants the image to align with `hermes-hudui` itself, with only one Ghostship-specific extension: a `Console` tab backed by `ttyd`.

This change is needed now because the current dashboard contract is intentionally not aligned with HUDUI's product shape, collectors, frontend behavior, or packaging model. Continuing to extend the current dashboard would deepen that divergence and make the later HUDUI migration harder.

This proposal does **not** define the upstream-aligned gateway-service migration. That work is happening in a separate change. This proposal consumes whatever managed gateway contract that change establishes and updates the browser/runtime integration around it.

## What Changes

- **BREAKING**: Replace the current packaged `hermes-dashboard` browser contract with a packaged `hermes-hudui`-aligned dashboard implementation.
- **BREAKING**: Replace the current Ghostship dashboard API contract, including `/api/status` and the current Ghostship HTML markers, with HUDUI's backend/frontend contract.
- **BREAKING**: Replace `ghostship-dashboard-controller.service` with a new HUDUI-specific managed browser service in the image runtime.
- Add one Ghostship-specific HUDUI extension: a `Console` tab that opens, proxies, and tears down on-demand `ttyd` sessions from the HUDUI surface.
- Keep the image on one managed agent rooted at `/home/hermes/.hermes`, but adapt the dashboard/runtime behavior so HUDUI can observe that layout cleanly.
- Add the runtime env and path wiring HUDUI needs, including a defined projects-directory contract for the HUDUI Projects panel.
- Replace the current dashboard smoke and persistence validation flows with HUDUI-aligned validation, including the new console-tab behavior.
- Update runtime docs, image docs, and OpenSpec requirements so the published browser contract matches HUDUI adoption rather than the old minimal dashboard.

## Capabilities

### New Capabilities
- None.

### Modified Capabilities
- `mmx-hermes-dashboard`: Replace the current MMX/minimal Ghostship dashboard contract with a HUDUI-aligned dashboard contract while adding a Ghostship `Console` tab for `ttyd`.
- `agent-workstation-runtime`: Replace the old dashboard-service assumptions with HUDUI service wiring, package layout, and projects-directory integration.
- `agent-workstation-updates`: Change operator validation expectations so they align with the new HUDUI browser surface and console-tab workflow.

## Impact

- Affected code: `packages/hermes-dashboard`, `packages/hermes-image/*`, `flake.nix`, dashboard frontend/backend tests, image smoke tests, persistence validation, and runtime docs.
- Affected systems: browser dashboard packaging, FastAPI service wiring, frontend asset build flow, `ttyd` proxy/session management, runtime validation, and image bootstrap environment wiring.
- Affected runtime contracts: browser entrypoint behavior, dashboard API shape, WebSocket update model, projects-directory discovery, systemd browser-service names, and operator documentation.
