## MODIFIED Requirements

### Requirement: Successful cold cache publication creates a consumable cache index
When a Ghostship workflow publishes store paths into `caelx/ghostship-cache`, a successful cold run SHALL create or update a `cache-index` manifest that later runs can detect before build start, and the publication path SHALL complete that index update without depending on shell argument sizes that scale with the number of uploaded entries.

#### Scenario: Cold run seeds the shared cache
- **WHEN** `publish-image` runs with an empty or previously missing shared cache and cache publication succeeds
- **THEN** the workflow publishes cache entries that create or update the `cache-index` manifest in `caelx/ghostship-cache`
- **AND** a later workflow run can detect that cache index during bootstrap

#### Scenario: Large cache publication updates the index successfully
- **WHEN** a cache-refresh run needs to publish a large set of Ghostship store paths
- **THEN** the shared-cache publication path completes the `cache-index` update without failing from command-line argument growth
- **AND** the resulting cache remains consumable by later runs

### Requirement: Shared cache consumption uses a local proxy backed by ghostship-cache
Ghostship GitHub Actions consumers SHALL access the shared cache through a runner-local proxy path backed by `caelx/ghostship-cache`, rather than by treating OCI images themselves as a substitute for a Nix binary cache. The consumer path SHALL keep the public-cache read path fast while allowing authenticated fallback when the cache backend or registry access rules require it.

#### Scenario: Consumer workflow configures the shared cache
- **WHEN** a Ghostship GitHub Actions workflow consumes the shared cache
- **THEN** the workflow starts or connects to a local cache proxy backed by `caelx/ghostship-cache`
- **AND** Nix is configured to use that local endpoint as a substituter during the build
- **AND** the workflow may still fall back to `cache.nixos.org` for public upstream paths

#### Scenario: Public cache bootstrap avoids unnecessary auth-only dependence
- **WHEN** `caelx/ghostship-cache` is publicly readable
- **THEN** shared-cache bootstrap can detect and consume the cache without requiring an extra auth-only probe in the common case
- **AND** authenticated registry access remains available as a fallback rather than the only supported read path
