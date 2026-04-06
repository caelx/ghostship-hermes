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
- **WHEN** a runtime seed directory exists at `/workspace/skills/shared/<skill>`
- **THEN** bootstrap copies that skill into `~/.hermes/skills/<skill>` only if the destination skill does not already exist

#### Scenario: Profile-specific skill root is available
- **WHEN** a runtime seed directory exists at `/workspace/skills/profiles/<profile>/<skill>` for one of the managed profiles
- **THEN** bootstrap copies that skill into `~/.hermes/profiles/<profile>/skills/<skill>` only if the destination skill does not already exist

#### Scenario: Existing Hermes-owned skills are preserved
- **WHEN** a skill destination already exists under `~/.hermes/skills/...` or `~/.hermes/profiles/<profile>/skills/...`
- **THEN** bootstrap leaves the existing destination unchanged even if the runtime seed source has been modified

### Requirement: The scaffold SHALL support a staged Hermes settings audit
The change process SHALL establish a stable generated scaffold first, then use that scaffold to drive the later bake-in of Hermes settings by category.

#### Scenario: First implementation pass generates the scaffold before final tuning
- **WHEN** maintainers begin implementation of this change
- **THEN** the first implementation step generates the basic three-profile scaffold in Nix
- **AND** later tasks iterate on model, auth, terminal, persona, env, and other Hermes settings from that scaffold rather than hand-editing one-off profile state
