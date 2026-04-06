## ADDED Requirements

### Requirement: The Hermes image SHALL provide a declarative three-profile scaffold
The Hermes image SHALL define a Nix-first managed profile scaffold for `assistant`, `operations`, and `supervisor`, and that scaffold SHALL be the single source of truth for generated profile metadata used by bootstrap and long-running profile services.

#### Scenario: Bootstrap materializes the approved managed profiles
- **WHEN** the image bootstraps the managed Hermes profile layout
- **THEN** the managed profile scaffold includes `assistant`, `operations`, and `supervisor`
- **AND** the scaffold identifies `assistant` as the sticky default profile
- **AND** the scaffold provides enough declarative metadata to generate each profile's config skeleton, env destination, skill destination, and gateway-service identity

### Requirement: Root Hermes config SHALL remain minimal
The image SHALL keep the root Hermes config minimal and SHALL treat the named managed profiles as the authoritative operator-facing runtime surface.

#### Scenario: Root config is present but not the primary workflow surface
- **WHEN** the image generates Hermes config content during bootstrap
- **THEN** the root config provides only the minimal baseline required for Hermes to start
- **AND** bootstrap activates `assistant` as the default working profile
- **AND** operators are expected to work through the named managed profiles rather than a richly tuned root profile

### Requirement: Shared and profile skills SHALL remain runtime-seeded and non-destructive
The image SHALL support shared and profile-specific skill seed roots from the runtime environment, and skill seeding SHALL copy only missing skill directories into Hermes-owned destinations without overwriting existing destinations.

#### Scenario: Shared skill root is available
- **WHEN** a runtime seed directory exists at `/home/hermes/seeds/shared/skills/<skill>`
- **THEN** bootstrap copies that skill into `~/.hermes/skills/<skill>` only if the destination skill does not already exist

#### Scenario: Profile-specific skill root is available
- **WHEN** a runtime seed directory exists at `/home/hermes/seeds/profiles/<profile>/skills/<skill>` for one of the managed profiles
- **THEN** bootstrap copies that skill into `~/.hermes/profiles/<profile>/skills/<skill>` only if the destination skill does not already exist
- **WHEN** a runtime seed file exists at `/home/hermes/seeds/profiles/<profile>/SOUL.md` for one of the managed profiles
- **THEN** bootstrap copies that file into `~/.hermes/profiles/<profile>/SOUL.md` only if the destination file does not already exist

#### Scenario: Existing Hermes-owned skills are preserved
- **WHEN** a skill destination already exists under `~/.hermes/skills/...` or `~/.hermes/profiles/<profile>/skills/...`
- **THEN** bootstrap leaves the existing destination unchanged even if the runtime seed source has been modified

### Requirement: The scaffold SHALL support a staged Hermes settings audit
The change process SHALL establish a stable generated scaffold first, then use that scaffold to drive the later bake-in of Hermes settings by category.

#### Scenario: First implementation pass generates the scaffold before final tuning
- **WHEN** maintainers begin implementation of this change
- **THEN** the first implementation step generates the basic three-profile scaffold in Nix
- **AND** later tasks iterate on model, auth, terminal, persona, env, and other Hermes settings from that scaffold rather than hand-editing one-off profile state

### Requirement: The scaffold SHALL support initial shared Hermes runtime defaults
The image SHALL allow a shared Nix-managed settings layer for all three managed profiles, while still leaving runtime secrets and mutable Hermes-owned state outside the image.

#### Scenario: Shared browser and security defaults are generated
- **WHEN** the image generates managed profile config for `assistant`, `operations`, and `supervisor`
- **THEN** each profile includes shared browser defaults with `browser.cloud_provider = "local"`
- **AND** the image includes `agent-browser` and `tirith` on the runtime PATH
- **AND** browser-provider env vars and one optional `BROWSER_CDP_URL` target can be passed through from the runtime environment without requiring Chrome or Chromium in the image

#### Scenario: Shared model and memory defaults are generated
- **WHEN** the image generates managed profile config for `assistant`, `operations`, and `supervisor`
- **THEN** each profile includes the current shared model defaults (`openai-codex/gpt-5.4`, `fallback_model = opencode-go/minimax-m2.7`, Gemini auxiliary overrides)
- **AND** each profile includes the current shared Holographic memory defaults without baking provider secrets into Nix
