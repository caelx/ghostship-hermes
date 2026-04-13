## Why

Upstream Hermes is currently failing to apply custom model switches reliably for Discord sessions, which makes the managed free-response channels drift away from the repo's intended routing behavior. This needs a repo-owned guard now so Discord free channels always stay on the local router path and operators stop carrying a dead Discord plugin path that never delivered the required behavior.

## What Changes

- Force managed Discord free-response channel sessions to use the local `ghostship-hermes-router` runtime path on every turn instead of allowing upstream session model-switch behavior to redirect them.
- Pin those Discord free-response turns to the repo-approved router alias rather than the direct upstream managed profile default.
- Prevent Discord free-response sessions from persisting or reusing incompatible per-session model overrides in that context.
- Remove the old repo-owned Discord plugin path that attempted to influence this behavior but never worked reliably.

## Capabilities

### New Capabilities
- `discord-free-channel-router`: Defines the managed runtime behavior that pins Discord free-response sessions to the local router and ignores incompatible session-scoped model switching in that context.

### Modified Capabilities
- `agent-workstation-runtime`: Remove the unsupported legacy Discord plugin path from the managed Hermes runtime surface so operators only rely on the supported router-pinned behavior.

## Impact

- Affected code: Hermes wrapper patching in `packages/hermes-agent-wrapped/package.nix`, managed runtime behavior in the bundled upstream gateway code, and any runtime validation that asserts Discord channel behavior.
- Affected systems: managed Discord gateway sessions, local router selection for Discord free-response traffic, and the supported managed Hermes runtime surface.
- Dependencies: no new auth or API-key contract, no new operator-facing env vars, and no change to the existing unauthenticated local router endpoint assumption.
