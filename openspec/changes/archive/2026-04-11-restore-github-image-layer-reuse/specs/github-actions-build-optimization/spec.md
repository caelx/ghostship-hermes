## MODIFIED Requirements

### Requirement: Architectural pipeline changes are allowed when they materially reduce build time
The repo SHALL allow architectural changes to the image build and publish pipeline when they materially reduce end-to-end time and preserve the explicit published image semantics.

#### Scenario: Maintainer proposes a faster image assembly path
- **WHEN** a maintainer identifies a materially faster image build or publication architecture
- **THEN** the repo may adopt that architecture if it preserves the explicit publishable image contract
- **AND** the optimization plan documents the trade-offs and verification needed for the new path

#### Scenario: Optimized publish path verifies the actual image under test
- **WHEN** the repo adopts a faster internal GitHub image assembly path
- **THEN** the workflow validates the exact assembled image before publication rather than relying only on checks for a different artifact path
- **AND** the optimization evidence continues to represent a correct publish path instead of a faster but unverified substitute
