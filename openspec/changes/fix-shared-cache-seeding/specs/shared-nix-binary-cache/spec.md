## ADDED Requirements

### Requirement: Successful cold cache publication creates a consumable cache index
When a Ghostship workflow publishes store paths into `caelx/ghostship-cache`, a successful cold run SHALL create or update a `cache-index` manifest that later runs can detect before build start.

#### Scenario: Cold run seeds the shared cache
- **WHEN** `publish-image` runs with an empty or previously missing shared cache and cache publication succeeds
- **THEN** the workflow publishes cache entries that create or update the `cache-index` manifest in `caelx/ghostship-cache`
- **AND** a later workflow run can detect that cache index during bootstrap

### Requirement: Shared cache verification distinguishes no-op uploads from real seeding
Ghostship shared-cache verification SHALL distinguish a no-op cache publish from a real seed event, rather than treating any successful upload step as proof that the cache is usable.

#### Scenario: Upload step exits successfully with no planned paths
- **WHEN** the shared-cache publication step has no planned paths to upload
- **THEN** maintainers do not treat that run as a seeded cache
- **AND** the workflow or runbook identifies that no consumable shared-cache index was produced from that run
