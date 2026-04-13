## MODIFIED Requirements

### Requirement: The dashboard exposes the managed agent runtime contract
The dashboard SHALL expose enough managed agent configuration through the upstream Hermes native dashboard pages and APIs to validate the live primary model, fallback model, env-backed configuration state, and gateway/session visibility for the managed runtime.

#### Scenario: Native dashboard exposes managed primary and fallback config
- **WHEN** the upstream Hermes dashboard reads the managed Hermes config in the published image
- **THEN** operators can inspect the managed primary model settings through native dashboard status/config surfaces
- **AND** operators can inspect the managed fallback model settings through native dashboard status/config surfaces
- **AND** the browser surface exposes the endpoint and runtime facts needed to validate the managed model contract without relying on Ghostship-only payloads

#### Scenario: Native dashboard exposes core managed operator pages
- **WHEN** an operator opens the published browser surface for the managed image
- **THEN** the upstream Hermes dashboard root loads successfully on port `9119`
- **AND** the native status, config, env, and sessions surfaces needed for runtime validation respond successfully
- **AND** the browser contract does not require custom `/api/health`, `/api/profiles`, `/api/projects`, or `/api/console` endpoints

#### Scenario: Deployed dashboard works in a cross-origin iframe
- **WHEN** maintainers load the deployed dashboard from `chill-penguin` inside an iframe hosted from a different origin
- **THEN** the dashboard renders successfully inside that iframe
- **AND** the embedded dashboard remains usable for broad upstream-native functions such as status, config, env, and session inspection
- **AND** the deployed response headers do not block the required iframe embed path

### Requirement: A healthy published image must prove the live runtime surface
The fix SHALL require post-publish and post-deploy validation against the upstream Hermes dashboard contract instead of assuming source changes reached the deployed artifact or proving health only through the retired custom dashboard APIs.

#### Scenario: Published image and deployed host are inspected directly
- **WHEN** maintainers publish and deploy the Hermes image
- **THEN** they inspect the published image for the intended model and runtime contract through the upstream Hermes dashboard and supporting CLI/service checks
- **AND** they verify on the deployed host that the browser entrypoint on `9119` serves the native Hermes dashboard and that the critical native dashboard surfaces respond
- **AND** they verify on `chill-penguin` that the deployed dashboard remains functional when embedded cross-origin in an iframe
- **AND** they verify that the router env disables `openrouter/free` and that `gateway.pid` survives `hermes doctor`
- **AND** they do not treat the rollout as healthy if the native dashboard path is broken even when the retired custom dashboard checks are gone
