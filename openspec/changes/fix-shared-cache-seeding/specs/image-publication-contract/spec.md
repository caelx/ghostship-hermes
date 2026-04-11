## ADDED Requirements

### Requirement: Cache upload planning happens before the real publish build when using a dry-run planner
If `publish-image` uses a cache planner that identifies upload candidates from `nix build --dry-run`, the workflow SHALL run that planning step before the real image build and carry the resulting plan forward to later cache publication.

#### Scenario: Cold run prepares upload candidates before build
- **WHEN** `publish-image` is about to build `ghostship-hermes-image` on a runner without a usable shared-cache index
- **THEN** the workflow computes the shared-cache upload plan before the real `nix build` starts
- **AND** the later cache publication step uses that saved plan instead of recomputing candidates after the build

### Requirement: Cache planning failure does not block image publication
`publish-image` SHALL continue to publish the explicit `ghostship-hermes-image` artifact even when shared-cache planning fails before the build starts.

#### Scenario: Pre-build cache planning fails
- **WHEN** the pre-build shared-cache planning step errors or times out
- **THEN** the workflow continues with the normal host-side image build and publication path
- **AND** it skips only the affected cache publication leg rather than failing image publication

### Requirement: Warm-cache reuse is observable in workflow evidence
The image publication workflow or its runbook SHALL provide maintainers enough evidence to tell whether a repeat publish consumed the shared cache, rather than relying only on final duration comparisons.

#### Scenario: Maintainer inspects a repeat publish run
- **WHEN** a maintainer reviews a repeat `publish-image` run after a successful cache seed
- **THEN** the run exposes whether shared-cache bootstrap succeeded before `nix build`
- **AND** the run provides log evidence that cached store paths were reused or that the build fell back to uncached behavior
