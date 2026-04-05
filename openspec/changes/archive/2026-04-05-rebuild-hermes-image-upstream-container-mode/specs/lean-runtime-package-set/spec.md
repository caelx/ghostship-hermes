## ADDED Requirements

### Requirement: Hermes image SHALL ship a lean default package set
The Hermes image SHALL bundle only the upstream Hermes runtime, runtime Nix support, the minimal browser terminal surface, and the retained repo-owned `ghostship-*` utilities in the default image package set.

#### Scenario: Lean image keeps required runtime packages
- **WHEN** maintainers inspect the rebuilt image package inventory
- **THEN** the image includes Hermes, `nix`, the minimal dashboard/runtime support, `ttyd`, and every repo-owned `ghostship-*` utility
- **AND** the image does not depend on a separate Ghostship-managed workstation app layer to make those retained tools available

### Requirement: Hermes image SHALL exclude legacy Ghostship workstation extras by default
The default image package set SHALL NOT preinstall Ghostship-managed workstation extras that are no longer part of the upstream-aligned runtime model.

#### Scenario: Removed workstation extras are absent
- **WHEN** maintainers inspect the rebuilt image contents and PATH
- **THEN** the default image does not preinstall `codex`, `gemini-cli`, `opencode`, `openspec`, `skills`, `gws`, `bws`, or `feed`
- **AND** the image does not include repo-managed workstation seed trees for those removed extras
