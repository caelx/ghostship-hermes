## Why

The current "MMX" dashboard uses a retro-cyberpunk aesthetic that, while functional, feels dated compared to modern UI trends. The user wants a "fresh and modern" look inspired by glassmorphism (transparency, blur, and refined typography) to improve the overall workstation experience while maintaining all existing terminal session management capabilities.

## What Changes

- **Redesign Dashboard UI**: Replace the high-contrast, neon "MMX" style with a modern "Hermes Glass" aesthetic.
- **Glassmorphism Foundation**: Implement a deep, atmospheric background with soft gradients and floating "aura" blobs to provide depth for glass effects.
- **Translucent Components**: Update the sidebar, terminal panels, and buttons to use `backdrop-filter: blur()`, semi-transparent backgrounds, and subtle borders.
- **Refined Typography**: Transition from retro-mono fonts to a modern variable sans-serif (e.g., Inter/Outfit) for UI controls, while keeping IBM Plex Mono for terminal content.
- **Modernized Copy**: Update military-style labels (e.g., `NEW_UNIT`, `TERMINATE_SESSION`) to cleaner, professional alternatives (e.g., `New Session`, `Close`).
- **Visual Verification**: Integrate `agent-browser` into the development/testing workflow to visually inspect and validate the new style within the containerized environment.

## Capabilities

### New Capabilities
- `glass-hermes-dashboard`: Defines the modern glassmorphism UI contract for the Hermes dashboard, specifying visual requirements, component styles, and atmospheric effects.

### Modified Capabilities
- `mmx-hermes-dashboard`: Deprecate the specific "MMX" visual requirements in favor of the new glass style, while preserving the underlying session management and proxying logic.

## Impact

- Affected code: `packages/hermes-dashboard/src/hermes_dashboard/static/*` (HTML, CSS, JS).
- Affected systems: The Hermes container's browser-facing UI.
- Dependencies: Requires modern browser support for `backdrop-filter` (already assumed for the current workstation target).
