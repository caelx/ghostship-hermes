## Why

The current dashboard home view reports only coarse runtime, provider, and profile facts, but the Hermes image now carries a much richer configuration surface around profiles, models, auxiliary tasks, memory, security, browser behavior, messaging, and runtime-backed integrations. Operators need an at-a-glance observability view that reflects the real Hermes runtime contract without hardcoding today’s profile names or breaking when the config grows.

## What Changes

- Expand the dashboard home payload from a narrow environment summary into grouped runtime and configuration sections that cover the effective Hermes settings operators care about, including profile topology, model path, auxiliary overrides, memory, security, browser, messaging, and env-backed capability presence.
- Redesign the home UI from three large panels into smaller feature-oriented cards that stack and reflow automatically as sections appear or disappear.
- Tighten terminal tab interactions so opening a terminal creates a visible tab immediately and closing a terminal removes it from the UI immediately, even if the backing `ttyd` process is still starting up or shutting down in the background.
- Raise the visual bar for the dashboard so it delivers a more distinctive futuristic Hermes aesthetic with intentional motion and stronger visual identity instead of a minimal utilitarian card layout.
- Make the dashboard render discovered profiles and section groups generically so added profiles, new config categories, and missing optional integrations do not break the page layout.
- Keep the dashboard read-only and secret-safe by exposing effective config state and env presence rather than raw secret values.
- Preserve router-specific enrichment as conditional behavior when Hermes is pointed at the local router, without making router data a prerequisite for the home view.

## Capabilities

### New Capabilities
- None.

### Modified Capabilities
- `mmx-hermes-dashboard`: Expand the dashboard home view into a generic Hermes runtime and configuration observability surface with modular cards and conditional router enrichment.

## Impact

- Affected code: `packages/hermes-dashboard/src/hermes_dashboard/app.py`, `packages/hermes-dashboard/src/hermes_dashboard/static/index.html`, `packages/hermes-dashboard/src/hermes_dashboard/static/app.js`, `packages/hermes-dashboard/src/hermes_dashboard/static/styles.css`, and dashboard tests.
- Affected runtime systems: dashboard environment/config payload generation, profile/service discovery, and optional router enrichment.
- Affected operator workflow: the browser dashboard becomes the primary at-a-glance surface for understanding effective Hermes configuration and runtime posture.
