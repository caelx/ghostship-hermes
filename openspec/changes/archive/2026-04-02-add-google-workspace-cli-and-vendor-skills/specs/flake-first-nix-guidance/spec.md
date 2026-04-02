## ADDED Requirements

### Requirement: Repo-managed Nix guidance is flake-first
The repo-managed Nix skill SHALL instruct agents to prefer flake-native commands for repo and image work, including `nix run`, `nix shell`, `nix develop`, and repo `.#` outputs.

#### Scenario: Repo workflows use flake-native commands
- **WHEN** an agent reads the repo-managed Nix guidance for running repo tools or building image outputs
- **THEN** the guidance directs the agent to use flake-native commands first
- **AND** the guidance references repo outputs through `.#` selectors for repo-owned tooling

### Requirement: Persistent user installs remain scoped to explicit Nix profile use
The repo-managed Nix guidance SHALL distinguish flake-native execution from persistent user installation and SHALL reserve `nix profile install` for tools that must survive restarts outside the repo build itself.

#### Scenario: Guidance separates execution from persistence
- **WHEN** an agent needs a one-off tool or repo-owned package
- **THEN** the guidance steers the agent toward `nix shell`, `nix run`, or `nix develop`
- **AND** it uses `nix profile install` only for explicit persistent user-level installs

### Requirement: Google Workspace integration docs describe flake-managed updates and auth constraints
Repo documentation SHALL explain that the Google Workspace CLI and vendored skills are updated through pinned flake revision changes and SHALL document Gmail narrow-scope guidance for testing-mode personal accounts.

#### Scenario: Maintainer follows documented update path
- **WHEN** a maintainer reads the documented Google Workspace integration workflow
- **THEN** the documentation instructs them to update the pinned flake revision and vendored skill snapshot together
- **AND** it describes the personal Gmail testing-mode scope constraint and the narrow-scope login path
