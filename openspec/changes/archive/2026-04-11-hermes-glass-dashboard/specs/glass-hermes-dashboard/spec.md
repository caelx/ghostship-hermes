## ADDED Requirements

### Requirement: Dashboard exposes a modern Hermes Glass visual identity
The Hermes dashboard SHALL present a modern glassmorphism visual identity instead of the earlier retro-MMX treatment while preserving the existing session-management and terminal-proxy behavior.

#### Scenario: Browser entrypoint renders glassmorphism surfaces
- **WHEN** an operator opens the Hermes dashboard in a supported browser
- **THEN** the packaged entrypoint renders translucent glass-style panels and controls
- **AND** the interface uses backdrop blur, subtle borders, and layered depth instead of the older neon/MMX chrome

#### Scenario: Dashboard uses a deep atmospheric background
- **WHEN** the dashboard entrypoint loads
- **THEN** the page renders a dark atmospheric background with soft gradient or aura effects that support the glass treatment
- **AND** the background remains decorative rather than obscuring runtime facts or terminal content

### Requirement: Dashboard copy and controls feel modern and operator-friendly
The dashboard SHALL use modern professional copy and refined controls instead of military-themed labels and retro control styling.

#### Scenario: Operator-facing labels use modern copy
- **WHEN** maintainers inspect the packaged dashboard entrypoint
- **THEN** operator-facing labels such as session creation, loading state, and terminal close actions use modern professional wording
- **AND** the UI no longer depends on MMX- or battle-station-style copy to communicate normal dashboard actions

#### Scenario: Session controls remain responsive under the new style
- **WHEN** an operator opens, switches, or closes terminal sessions from the dashboard
- **THEN** the refined glass-styled controls still expose those actions clearly
- **AND** state transitions remain visually responsive while preserving the existing underlying behavior
