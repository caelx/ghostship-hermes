## MODIFIED Requirements

### Requirement: Publishable image artifact preserves the workstation runtime contract
The repo SHALL derive the publishable `ghostship-hermes` image artifact from the workstation runtime source artifact through a repo-owned conversion path that preserves the documented container metadata, OCI provenance labels, and the final managed runtime bootstrap behavior.

#### Scenario: Published image keeps expected runtime metadata
- **WHEN** maintainers build or publish the explicit publishable image artifact
- **THEN** the resulting image starts with `/init` as the runtime entry path
- **AND** the resulting image preserves the documented runtime defaults such as `HOME=/home/hermes`, `HERMES_HOME=/home/hermes/.hermes`, and port `7681`
- **AND** the resulting image includes OCI labels that identify the source repository URL and source revision in addition to the documented title, description, and version labels

#### Scenario: Published image keeps managed runtime bootstrap behavior
- **WHEN** maintainers publish `ghostship-hermes` to GHCR or export the explicit publishable image bundle locally
- **THEN** the resulting image preserves the final repo-owned managed runtime wiring that rewrites `/home/hermes/.hermes/.env`
- **AND** the resulting image preserves the root seed consumption behavior for `/home/hermes/.hermes/skills` and `/home/hermes/.hermes/SOUL.md`
- **AND** the published image does not silently fall back to a different upstream-only Hermes activation path
