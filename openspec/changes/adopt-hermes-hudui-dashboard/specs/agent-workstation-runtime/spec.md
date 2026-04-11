## ADDED Requirements

### Requirement: Managed browser service runs HUDUI as the canonical dashboard
The workstation SHALL run a HUDUI-specific managed browser service as the canonical browser entrypoint for the image runtime, replacing the previous Ghostship dashboard-controller service contract.

#### Scenario: Boot starts the HUDUI browser service
- **WHEN** the container boots the managed Hermes services
- **THEN** the managed browser service starts the packaged HUDUI dashboard on the published browser port
- **AND** the image no longer requires the previous `ghostship-dashboard-controller.service` contract to reach the browser surface

#### Scenario: Browser service runs the packaged dashboard artifact
- **WHEN** maintainers inspect the managed browser-service command path
- **THEN** the service executes the packaged HUDUI-derived dashboard artifact from the image build
- **AND** the runtime does not depend on a mutable repo checkout or ad hoc frontend build step inside the container

### Requirement: Runtime defines a HUDUI projects root for the image
The workstation SHALL define an explicit HUDUI projects-directory contract that maps the dashboard's Projects panel to the image's persisted work-products mount.

#### Scenario: HUDUI projects panel reads from the persisted workspace mount
- **WHEN** the managed browser service starts inside the image runtime
- **THEN** the runtime exposes a HUDUI projects root that points at `/workspace`
- **AND** the HUDUI Projects panel does not have to fall back to `~/projects` to discover operator workspaces

#### Scenario: Project discovery stays separate from Hermes state
- **WHEN** operators inspect the runtime layout used by the HUDUI dashboard
- **THEN** the projects root remains distinct from `/home/hermes/.hermes`
- **AND** the browser contract does not require work-product repositories to live inside the managed Hermes state directory

### Requirement: Managed browser packaging includes the HUDUI frontend build output
The workstation SHALL package the browser artifact with the compiled HUDUI frontend assets it serves at runtime.

#### Scenario: Built package contains HUDUI static assets
- **WHEN** maintainers build the packaged dashboard artifact directly
- **THEN** the resulting package includes the compiled frontend assets needed by the HUDUI browser service
- **AND** the runtime does not depend on unbuilt development-only frontend sources to serve the dashboard
