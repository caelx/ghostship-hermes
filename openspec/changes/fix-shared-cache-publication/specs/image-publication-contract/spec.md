## MODIFIED Requirements

### Requirement: Cache planning failure does not block image publication
`publish-image` SHALL continue to publish the explicit `ghostship-hermes-image` artifact even when shared-cache planning fails before the build starts, and the workflow SHALL avoid adding extra steady-state verification work solely to prove cache behavior.

#### Scenario: Pre-build cache planning fails
- **WHEN** the pre-build shared-cache planning step errors or times out
- **THEN** the workflow continues with the normal host-side image build and publication path
- **AND** it skips only the affected cache publication leg rather than failing image publication

#### Scenario: Cache proof does not add another workflow stage
- **WHEN** maintainers need to prove that shared-cache reuse works
- **THEN** they use existing run evidence from seeded and repeat publish runs
- **AND** the workflow does not add a dedicated extra proof job or verification stage that increases normal publish latency

### Requirement: Warm-cache reuse is observable in workflow evidence
The image publication workflow or its runbook SHALL provide maintainers enough evidence to tell whether a repeat publish consumed the shared cache, rather than relying only on final duration comparisons. That evidence SHALL come from the normal publish logs and manual run inspection rather than from new workflow work added only for proof.

#### Scenario: Maintainer inspects a repeat publish run
- **WHEN** a maintainer reviews a repeat `publish-image` run after a successful cache seed
- **THEN** the run exposes whether shared-cache bootstrap succeeded before `nix build`
- **AND** the run provides log evidence that cached store paths were reused or that the build fell back to uncached behavior

#### Scenario: Manual proof uses existing workflow evidence
- **WHEN** Codex or a maintainer proves the shared cache manually
- **THEN** the proof compares an explicit seeded run with an unchanged repeat run
- **AND** it relies on existing plan, bootstrap, and build log evidence instead of adding new steady-state workflow steps
