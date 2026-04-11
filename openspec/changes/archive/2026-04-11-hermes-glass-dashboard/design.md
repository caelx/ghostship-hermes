## Context

The current dashboard in `packages/hermes-dashboard` uses a retro-cyberpunk "MMX" theme. While functional, it feels dated. The goal is to move to a "Glassmorphism" aesthetic: a modern, light-weight, and visually sophisticated design characterized by transparency, layered depth, and blurred backgrounds.

## Goals / Non-Goals

**Goals:**
- **Modern Aesthetic**: Implement "Hermes Glass" using `backdrop-filter`, transparency, and subtle borders.
- **Deep Atmospheric Background**: Create a dark, colorful background that provides the necessary contrast for the glass effect.
- **Clean Typography**: Transition from retro-mono to a modern variable sans-serif for UI elements.
- **Maintain Functionality**: Ensure terminal session management and proxying continue to work perfectly.
- **Visual Validation**: Use `agent-browser` to confirm the final visual state.

**Non-Goals:**
- **Rewriting the Backend**: The Python/FastAPI logic remains unchanged.
- **Changing the JS Logic**: The polling and state management in `app.js` will be preserved, only class names and labels will be updated.
- **External Asset Dependencies**: Prefer CSS-native effects (gradients, blurs) over external images where possible.

## Decisions

### 1. Atmosphere: "Nebula" Background
**Rationale:** Glassmorphism requires a colorful, high-contrast background to truly shine.
- **Choice**: A deep indigo/charcoal background (`#0a0a0c`) with two or three large, soft CSS-radial-gradient "blobs" (cyan and violet) that are fixed in the background.
- **Alternative**: A static image background. Rejected to keep the bundle size small and the design more flexible.

### 2. Surfaces: Layered Glass
**Rationale:** Creates a sense of hierarchy and depth.
- **Choice**: Use a consistent `.glass-pane` class for all major containers (sidebar, stage).
  ```css
  background: rgba(255, 255, 255, 0.03);
  backdrop-filter: blur(24px) saturate(160%);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 20px;
  ```
- **Rationale**: 24px blur provides a sophisticated "frosted" look without being too noisy.

### 3. Typography: Professional Sans
**Rationale**: Retro-mono is too aggressive for a "modern" feel.
- **Choice**: Use **Inter** (via Google Fonts) as the primary UI font. It's clean, legible, and modern.
- **Secondary**: Maintain **IBM Plex Mono** for the terminal and labels where "tech" precision is still appropriate.

### 4. Component Layout: Floating Panels
**Rationale**: Enhances the "floating glass" feeling.
- **Choice**: The sidebar and main stage will have generous margins (`16px`) and rounded corners, making them appear to float above the background rather than being fixed edges.

## Risks / Trade-offs

- **[Risk] Performance**: Large `backdrop-filter` blurs can be GPU-intensive.
- **[Mitigation]**: Keep the number of layers low and avoid animating the blur itself.
- **[Risk] Visibility**: Glass effects can sometimes make text hard to read.
- **[Mitigation]**: Ensure high-contrast text (pure white or very light cyan) and use a dark enough background tint in the glass panes.
