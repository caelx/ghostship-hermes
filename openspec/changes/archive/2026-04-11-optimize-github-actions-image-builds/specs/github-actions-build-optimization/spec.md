## ADDED Requirements

### Requirement: GitHub Actions build optimization is measured in explicit rounds
The repo SHALL optimize GitHub Actions build and publication performance through explicit baseline capture and multiple implementation rounds instead of an unmeasured one-shot workflow rewrite.

#### Scenario: Maintainer starts the optimization effort
- **WHEN** a maintainer begins work on GitHub Actions build-performance improvements
- **THEN** the repo defines a recorded baseline for the current `ci` and `publish-image` workflows
- **AND** the repo defines at least one subsequent optimization round whose results can be compared against that baseline

### Requirement: Each optimization round records comparable timing evidence
Each optimization round SHALL record timing evidence that lets maintainers compare the previous and current workflow behavior for the same major paths.

#### Scenario: Maintainer evaluates an optimization round
- **WHEN** a maintainer reviews the outcome of an optimization round
- **THEN** the repo provides comparable timing data for `ci` and `publish-image`
- **AND** the data distinguishes whole-workflow elapsed time from at least the major slow jobs inside the publish path

### Requirement: Optimization work targets a 10-minute publish stretch goal without weakening correctness
The optimization effort SHALL target an approximately 10-minute end-to-end image publish path as a stretch goal while preserving multi-arch publication correctness and the repo's explicit image contract.

#### Scenario: Optimization round improves speed
- **WHEN** a maintainer lands an optimization round that changes the image build or publish path
- **THEN** the round is evaluated against the stretch goal of about 10 minutes for the publish path
- **AND** the round still verifies native multi-arch publication behavior and the declared `ghostship-hermes-image` artifact contract

### Requirement: Architectural pipeline changes are allowed when they materially reduce build time
The repo SHALL allow architectural changes to the image build and publish pipeline when they materially reduce end-to-end time and preserve the explicit published image semantics.

#### Scenario: Maintainer proposes a faster image assembly path
- **WHEN** a maintainer identifies a materially faster image build or publication architecture
- **THEN** the repo may adopt that architecture if it preserves the explicit publishable image contract
- **AND** the optimization plan documents the trade-offs and verification needed for the new path
