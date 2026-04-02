## ADDED Requirements

### Requirement: Repo-managed service skills SHALL use workflow-oriented family templates
The repo-managed service skills SHALL be rewritten around a small set of family templates that structure guidance around full operator workflows instead of flat command catalogs.

#### Scenario: media manager skills share a common workflow structure
- **WHEN** a user opens any rewritten media manager skill
- **THEN** the skill MUST use the media-manager family structure
- **THEN** the guidance MUST still be specific to that service's domain

#### Scenario: download and infra skills use different workflow structures
- **WHEN** a user opens rewritten skills from different service families
- **THEN** the skills MUST follow family-specific workflow structures rather than one universal template

### Requirement: Rewritten skills SHALL emphasize safe full operator workflows
Each rewritten service skill SHALL guide the agent through safe end-to-end workflows that include inspection, targeted mutation where relevant, and post-change verification.

#### Scenario: write-capable skill includes mutation flow
- **WHEN** a rewritten service skill covers write or delete operations
- **THEN** it MUST direct the agent to inspect current state before mutation
- **THEN** it MUST direct the agent to use `--dry-run` where the CLI supports it
- **THEN** it MUST direct the agent to verify post-state after the mutation

#### Scenario: read-first diagnosis workflow is available
- **WHEN** an agent needs to diagnose a service problem
- **THEN** the skill MUST provide a read-first workflow for health, queue, history, or equivalent inspection before recommending mutations

### Requirement: Rewritten skills SHALL preserve domain-specific guidance
The rewritten skill pack SHALL preserve domain-specific operator guidance for each service instead of collapsing all skills into generic wording.

#### Scenario: service-specific sequencing is retained
- **WHEN** two rewritten skills belong to the same family
- **THEN** they MAY share section structure
- **THEN** they MUST still describe service-specific starting points, workflow ordering, and common mistakes

### Requirement: Selected skills SHALL remain bespoke
The skills whose value comes from environment or specialized workflow guidance SHALL remain bespoke instead of being forced into the family-template structure.

#### Scenario: workflow-specialized skills remain custom
- **WHEN** the skill pack is rewritten
- **THEN** `current-environment`, `hermes-nix`, `pricebuddy`, and `rss-bridge` MUST retain bespoke guidance tailored to their domain

### Requirement: The repo `agent-browser` skill SHALL be replaced with the provided upstream content unchanged
The `skills/agent-browser/SKILL.md` file SHALL be replaced with the provided upstream `agent-browser` skill content without repo-specific rewriting.

#### Scenario: agent-browser is copied through
- **WHEN** the skill rewrite is applied
- **THEN** `skills/agent-browser/SKILL.md` MUST match the provided upstream content for this change
