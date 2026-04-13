## ADDED Requirements

### Requirement: Repo-owned runtime wrappers SHALL honor an operator-facing help contract
Repo-owned runtime wrapper binaries shipped in the Hermes image SHALL provide a non-destructive help or usage surface.

#### Scenario: Router wrapper prints help without starting the server
- **WHEN** an operator invokes `ghostship-hermes-router --help`
- **THEN** the wrapper SHALL print help or usage information and exit successfully
- **AND** it SHALL not start the router server, perform remote inventory refreshes, or fail by colliding with the active router port

#### Scenario: Runtime wrapper provides explicit usage behavior
- **WHEN** an operator invokes `ghostship-hermes-runtime --help`
- **THEN** the wrapper SHALL present clear usage information for its supported subcommands
- **AND** the help path SHALL be intentionally documented so it can be validated consistently in the live CLI audit
