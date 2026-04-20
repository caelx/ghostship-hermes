## MODIFIED Requirements

### Requirement: The dashboard exposes the managed agent runtime contract
The dashboard SHALL expose enough managed agent configuration through the upstream Hermes native dashboard plus the repo-owned `Terminal` entry to validate the live model contract, gateway visibility, router presence, and browser-terminal availability for the managed runtime, without requiring a repo-owned browser live-view path.

#### Scenario: Native dashboard exposes managed runtime facts
- **WHEN** an operator opens the published browser surface for the managed image
- **THEN** the upstream Hermes dashboard root loads successfully on the supported dashboard port
- **AND** the native status, config, env, and sessions surfaces needed for runtime validation respond successfully
- **AND** the browser contract does not require the retired custom dashboard APIs
- **AND** the browser contract does not require a repo-owned `/camofox/` browser iframe path

#### Scenario: Patched terminal flow remains available
- **WHEN** an operator opens the `Terminal` entry from the published browser surface
- **THEN** the dashboard reaches a working `ttyd` terminal session through the published `/terminal/` path
- **AND** the published image proves that browser-terminal access still works through the supported patched terminal contract

## ADDED Requirements

### Requirement: Live host validation on `chill-penguin` proves the native browser replacement
The workstation SHALL require manual live-host validation on `chill-penguin` for the native CloakBrowser browser contract in addition to image-local automation.

#### Scenario: `chill-penguin` validation proves the browser replacement end to end
- **WHEN** maintainers validate the browser-contract replacement on the deployed host
- **THEN** they manually exercise the supported native browser path on `chill-penguin`
- **AND** they verify that the upstream Hermes dashboard and patched terminal path still work on that host
- **AND** they verify that the supported browser profile at `/home/hermes/.local/state/cloakbrowser` survives restart or full container recreation on that host
