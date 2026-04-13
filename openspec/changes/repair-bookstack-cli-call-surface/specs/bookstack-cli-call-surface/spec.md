## ADDED Requirements

### Requirement: BookStack passthrough and text-response commands SHALL execute through the shared client contract
The `ghostship-bookstack` utility SHALL support the generic `request` command and text-response operations using the same shared request signature that powers typed JSON operations.

#### Scenario: Generic request command succeeds for a read-only BookStack endpoint
- **WHEN** an operator invokes `ghostship-bookstack request GET /books` with valid runtime configuration
- **THEN** the command SHALL issue the request without a client-signature error
- **AND** the command SHALL emit the decoded upstream response using the repo's JSON-first output contract

#### Scenario: Text-response command returns the docs payload
- **WHEN** an operator invokes `ghostship-bookstack docs_display` against a reachable BookStack API origin
- **THEN** the command SHALL complete without raising an unexpected keyword-argument error
- **AND** the command SHALL return text-response metadata and body content that represent the upstream docs page

### Requirement: BookStack API-surface validation SHALL cover the shipped command paths
The repo SHALL test the shipped BookStack call surface at the failure boundary that was observed in deployment.

#### Scenario: Regression tests cover typed, passthrough, and text-response paths
- **WHEN** maintainers run the BookStack package test suite
- **THEN** the suite SHALL cover at least one typed JSON operation, the generic `request` command, and a text-response command such as `docs_display`
- **AND** the suite SHALL fail if a derived client drifts from the shared request signature

#### Scenario: Runtime topology is explicit during smoke validation
- **WHEN** operators validate `ghostship-bookstack` in a deployed Hermes image
- **THEN** the documented smoke workflow SHALL confirm whether `BOOKSTACK_URL` targets a reachable BookStack API origin or an auth gateway
- **AND** the validation output SHALL make configuration failures distinguishable from CLI implementation defects
