## MODIFIED Requirements

### Requirement: Downstream docs define the supported operator-facing env inventory
The workstation docs SHALL enumerate the supported downstream-owned operator env inventory and how to supply it for the new container contract.

#### Scenario: Operator follows the env documentation
- **WHEN** a downstream operator reads the deployment guidance for the workstation image
- **THEN** the docs identify which env values are downstream-owned
- **AND** the docs show how to provide those values through Compose, `docker run`, or a persisted operator-managed env file under `/home/hermes/.hermes`
- **AND** the docs distinguish operator-facing env from image-internal plumbing env
- **AND** the docs identify `DISCORD_HOME_CHANNEL` as required downstream env when the Discord gateway is enabled
- **AND** the docs identify `GHOSTSHIP_ROUTER_CHANNEL` as the only downstream-owned Discord channel pin env in the supported contract
- **AND** the docs identify `GHOSTSHIP_CODEX_CHANNEL` as removed from the supported downstream env contract
- **AND** the docs explain that Codex auth remains persisted home state rather than a downstream env key
