## MODIFIED Requirements

### Requirement: Image publication reuses supported cached build outputs
GitHub Actions image publication SHALL reuse supported cache or substituter-backed build outputs when the relevant inputs are unchanged, instead of rebuilding unchanged image dependencies from scratch on every run.

#### Scenario: Publish workflow repeats with unchanged build inputs
- **WHEN** the image publish workflow runs again with unchanged inputs for a previously built dependency or image closure
- **THEN** the workflow reuses the supported cached output where available
- **AND** the workflow still produces the same explicit publishable image contract

#### Scenario: Publish workflow consumes the shared Ghostship cache
- **WHEN** `publish-image` is configured to use `caelx/ghostship-cache`
- **THEN** the workflow consumes cached Nix store paths through the supported shared-cache proxy/substituter path
- **AND** it still builds the explicit `ghostship-hermes-image` bundle on the runner host before export/publication

#### Scenario: Shared-cache miss falls back to the normal publish path
- **WHEN** the shared Ghostship cache is empty or unavailable before the publish build starts
- **THEN** `publish-image` continues with the normal full host-side build path
- **AND** it does not switch to a different image assembly architecture or publish a different artifact contract
