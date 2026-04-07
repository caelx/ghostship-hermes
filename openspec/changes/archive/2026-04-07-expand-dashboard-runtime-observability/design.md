## Context

The current dashboard backend produces a small environment summary centered on runtime facts, providers, and profile endpoint settings. The frontend renders that payload into three large home panels, with the profiles panel forced to span full width. That shape worked for the earlier image contract, but it is no longer enough for the current Hermes runtime, which now has meaningful operator-facing configuration around multiple managed profiles, model routing, auxiliary tasks, memory, security, browser defaults, messaging gateways, and optional local-router enrichment.

The dashboard needs to stay generic. The new Hermes image already moved beyond the older `operations` and `coder` assumptions, and future changes may add or remove profiles, integrations, or config categories. The browser home view therefore needs to be driven by discovered profile and section data rather than fixed card names or profile identifiers.

## Goals / Non-Goals

**Goals:**
- Expand the backend payload into grouped runtime and configuration sections that reflect the effective Hermes contract operators care about.
- Keep the dashboard read-only and secret-safe by exposing resolved config state and env presence rather than raw secret values.
- Replace the three large home panels with smaller feature-oriented cards that auto-flow and stack cleanly across different viewport sizes.
- Render profiles, integrations, and config groups generically so the home view tolerates added profiles and optional features.
- Preserve router enrichment as conditional metadata when the configured model path points at the local router.

**Non-Goals:**
- Turn the dashboard into a config editor or settings management surface.
- Change the router API contract or require router presence for the home view.
- Expose secret values, tokens, or raw credential material in the browser.

## Decisions

### Group dashboard data by feature area instead of flat summary keys
The backend should emit grouped sections such as `runtime`, `paths`, `profiles`, `models`, `auxiliary`, `memory`, `security`, `browser`, `messaging`, and `env_presence`. Each section should contain the effective facts the operator would want to inspect, with optional sections omitted when the runtime does not provide the data.

Alternative considered: continue extending the existing flat payload with more top-level keys. Rejected because it would make both the payload and the frontend rendering brittle as new concerns are added.

### Make the frontend a section-renderer pipeline
The frontend home view should iterate through typed section renderers and only display cards for sections that are present. Each renderer should accept structured data, return `null` when it is not applicable, and avoid assumptions about specific profile names or fixed card ordering.

Alternative considered: keep a single monolithic `renderHome()` with hardcoded `Runtime`, `Providers`, and `Profiles` blocks. Rejected because it does not scale to the richer config surface and makes responsive layout awkward.

### Use smaller cards in a dense responsive grid
The layout should move from the current special-case two-column grid to a generic auto-fit card layout with smaller feature cards. The cards should be designed to compose naturally so that runtime, model, memory, browser, messaging, and profile information can stack and wrap without one oversized panel dominating the page.

Alternative considered: keep the current large-card layout and add more rows below it. Rejected because it would create a long, visually heavy home page that still breaks badly when sections appear or disappear.

### Make terminal tabs optimistic in the UI
Opening a terminal should create and focus a dashboard tab immediately, with the embedded terminal view transitioning into the live `ttyd` session as soon as it is available. Closing a terminal should remove its tab from the visible UI immediately while the backend tears down the corresponding `ttyd` process asynchronously.

Alternative considered: wait for `ttyd` startup and shutdown to complete before reflecting the tab change in the UI. Rejected because it makes the dashboard feel laggy and amplifies backend process latency into the user experience.

### Adopt a more distinctive Hermes visual language
The dashboard redesign should use a stronger futuristic Hermes aesthetic with deliberate typography, layered surfaces, atmospheric background treatment, and restrained but noticeable animations for section reveals, terminal-tab state transitions, and live-status changes. The visuals should remain reusable and data-driven rather than relying on one-off markup per section.

Alternative considered: keep a plain utilitarian card system with minimal motion. Rejected because it does not match the desired Hermes identity and makes the browser surface feel generic despite the richer runtime data.

### Expose presence and posture, not secrets
The dashboard should show whether integrations or auth-backed capabilities are configured, which provider path is active, and what posture is enabled for memory, security, browser, and messaging. It should not render secret values, bearer tokens, or raw `.env` contents.

Alternative considered: render raw env-derived config directly. Rejected for both security and readability reasons.

### Keep router enrichment conditional and additive
When the configured model endpoint is the local router, the dashboard should continue enriching the home view with router alias inventory and provider health. When the endpoint is not the local router, or router enrichment fails, the dashboard should still render the generic grouped configuration view without error.

Alternative considered: merge router-specific information into the generic payload unconditionally. Rejected because the dashboard must remain useful for direct-provider Hermes configs.

## Risks / Trade-offs

- [The new home view becomes too dense] → Keep the cards small, sectioned by feature area, and omit empty sections instead of rendering placeholder noise.
- [Backend payload growth makes the frontend brittle] → Use grouped, typed sections and keep each renderer tolerant of missing or extra keys.
- [Operators misread env presence as usable credentials] → Label env-backed capability cards as presence/status only and avoid rendering secret material.
- [Router-specific details leak into generic UX again] → Keep router sections conditional and separate from the provider-agnostic runtime/config cards.
- [Card proliferation hurts scanability] → Establish a stable feature-card hierarchy with concise labels and dense fact rows rather than verbose prose inside cards.
- [Optimistic terminal tabs drift from backend state] → Keep terminal cards explicitly marked as connecting or closing until the backend confirms the new state, and reconcile failed startups or teardowns cleanly.
- [A more expressive visual system harms readability] → Use motion and atmospheric styling to reinforce hierarchy, while preserving strong contrast and compact fact presentation inside each card.

## Migration Plan

1. Extend the dashboard backend payload so it can emit grouped runtime/config sections alongside the existing high-signal data.
2. Refactor the frontend home view into reusable section renderers, switch the layout to a generic auto-flow card grid, and add a more distinctive Hermes visual system with purposeful motion.
3. Add new cards for profile topology, model path, auxiliary overrides, memory, security, browser, messaging, env presence, and router enrichment, and make terminal tab open/close behavior feel immediate in the UI.
4. Update smoke tests and docs to reflect the new operator-facing dashboard contract.
5. Keep the page usable throughout the transition by retaining generic fallback rendering when optional sections are absent.

## Open Questions

- Which config groups deserve dedicated specialized cards versus generic key/value fallback cards on the first pass?
- How much profile detail should appear in the top-level home view before the page becomes too dense for operators?
- Whether any router alias or candidate inventory should move behind an expandable details view if the live data grows substantially.
