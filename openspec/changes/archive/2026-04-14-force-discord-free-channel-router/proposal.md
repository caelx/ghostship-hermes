## Why

Upstream Hermes is currently failing to apply custom model switches reliably for Discord sessions, which makes the managed free-response channels drift away from the repo's intended routing behavior. Hermes 0.9 improves upstream custom-provider handling, but it still does not provide a declarative "this Discord channel is always pinned to the router alias" control and it still keeps session-scoped model override behavior in the gateway. This change therefore still needs a repo-owned gateway guard so Discord free channels always stay on the local router path, while operators stop carrying a dead Discord plugin path that never delivered the required behavior.

## What Changes

- Force managed Discord free-response channel sessions to use the local `ghostship-hermes-router` runtime path on every turn instead of allowing upstream session model-switch behavior to redirect them.
- Pin those Discord free-response turns to the repo-approved router alias rather than the direct upstream managed profile default.
- Prevent Discord free-response sessions from persisting or reusing incompatible per-session model overrides in that context.
- Remove the old repo-owned Discord plugin path that attempted to influence this behavior but never worked reliably.
- Keep the Hermes 0.9 wrapper delta narrow: preserve the gateway pin, but do not carry forward the old repo-owned doctor patching now that upstream covers the OpenCode Go doctor surface itself.

## Capabilities

### New Capabilities
- `discord-free-channel-router`: Defines the managed runtime behavior that pins Discord free-response sessions to the local router and ignores incompatible session-scoped model switching in that context.

### Modified Capabilities
- `agent-workstation-runtime`: Remove the unsupported legacy Discord plugin path from the managed Hermes runtime surface so operators only rely on the supported router-pinned behavior.

## Impact

- Affected code: Hermes wrapper patching in `packages/hermes-agent-wrapped/package.nix`, managed runtime behavior in the bundled upstream gateway code, and any runtime validation that asserts Discord channel behavior.
- Affected systems: managed Discord gateway sessions, local router selection for Discord free-response traffic, and the supported managed Hermes runtime surface.
- Dependencies: no new auth or API-key contract, no new operator-facing env vars, and no change to the existing unauthenticated local router endpoint assumption.
- Upstream alignment note: Hermes 0.9 already carries the OpenCode Go doctor knowledge and native custom-provider plumbing, so the repo-owned patch surface should stay limited to the Discord router-channel enforcement and related validation.

## Follow-Up

During live rollout on `chill-penguin`, the new image was pulled and started, but the persisted managed Nix profile under `/home/hermes/.local/state/nix/profiles/ghostship-managed` was still pointing at an older `hermes-agent-wrapped` generation. That left the running gateway on stale wrapper code until the managed user-tooling convergence service was run and the container was restarted. A follow-up change should make image rollout converge the managed profile and restart the live gateway path automatically so future deploys cannot leave `/home/hermes` on an older Hermes wrapper generation.
