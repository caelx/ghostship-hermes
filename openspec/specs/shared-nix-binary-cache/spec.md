# shared-nix-binary-cache Specification

## Purpose
TBD - created by archiving change fix-shared-cache-seeding. Update Purpose after archive.
## Requirements
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

### Requirement: Ghostship maintains a dedicated shared Nix binary cache repo
The Ghostship project SHALL maintain `caelx/ghostship-cache` as a dedicated shared Nix binary cache backend for Ghostship Nix repositories instead of treating any single application repo as the cache-of-record.

#### Scenario: Maintainer inspects the cache repo contract
- **WHEN** a maintainer reads the `ghostship-cache` repo docs or operational guidance
- **THEN** the repo is described as shared cache infrastructure for Ghostship Nix projects
- **AND** the docs identify approved publisher and consumer repos or the policy for granting that access

#### Scenario: Multiple Ghostship repos may share the same cache backend
- **WHEN** a second Ghostship Nix repo is onboarded to the shared cache
- **THEN** it uses the same `ghostship-cache` backend contract rather than requiring a separate per-project cache repo
- **AND** unchanged store paths may be reused across projects when their derivations match

### Requirement: Shared cache consumption uses a local proxy backed by ghostship-cache
Ghostship GitHub Actions consumers SHALL access the shared cache through a runner-local proxy path backed by `caelx/ghostship-cache`, rather than by treating OCI images themselves as a substitute for a Nix binary cache.

#### Scenario: Consumer workflow configures the shared cache
- **WHEN** a Ghostship GitHub Actions workflow consumes the shared cache
- **THEN** the workflow starts or connects to a local cache proxy backed by `caelx/ghostship-cache`
- **AND** Nix is configured to use that local endpoint as a substituter during the build
- **AND** the workflow may still fall back to `cache.nixos.org` for public upstream paths

### Requirement: Shared Ghostship cache uses signing-based trust
The shared Ghostship cache SHALL use a signing-based trust model with one documented public key that consumer repos trust and publisher workflows use indirectly through the approved signing configuration.

#### Scenario: Consumer repo verifies the shared cache
- **WHEN** a Ghostship repo is configured to consume `ghostship-cache`
- **THEN** its Nix configuration trusts the documented `ghostship-cache` public key
- **AND** the repo does not need to disable signature verification broadly to consume the cache

#### Scenario: Publisher workflow populates the shared cache
- **WHEN** an approved Ghostship repo publishes store paths into `ghostship-cache`
- **THEN** the publication uses the configured signing path for that shared cache
- **AND** later consumer workflows can verify those paths with the documented public key

### Requirement: Cache unavailability may degrade to uncached builds without changing artifact semantics
Ghostship consumer workflows SHALL be allowed to fall back to uncached builds when the shared cache is cold or unavailable, provided they still build the same declared artifacts and do not silently weaken trust verification.

#### Scenario: Shared cache is cold or unavailable before build starts
- **WHEN** a consumer workflow cannot bootstrap the shared cache proxy or finds no reusable paths yet
- **THEN** the workflow may continue with its normal uncached build path
- **AND** the resulting build artifacts still follow the same repo-defined publication contract

#### Scenario: Shared cache returns untrusted results
- **WHEN** the shared cache path produces a signing or trust mismatch
- **THEN** the consumer workflow fails instead of silently accepting untrusted artifacts

