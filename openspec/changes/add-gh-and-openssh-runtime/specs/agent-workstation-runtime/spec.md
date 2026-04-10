## MODIFIED Requirements

### Requirement: Runtime keeps only a minimum viable immutable system layer
The workstation SHALL keep only the minimum system-layer packages needed to boot, supervise services, expose the browser/router runtime surface, and provide a small approved set of baked admin/debug CLIs.

#### Scenario: Most user-facing tools live outside the immutable system layer
- **WHEN** maintainers inspect the runtime contract for Hermes and operator-facing CLI tools
- **THEN** the immutable image layer does not remain the primary home for broadly updateable user-facing tools such as `hermes`, `curl`, `jq`, `python3`, `nix`, `ripgrep`, and `node`/`npm`
- **AND** those tools are instead expected through managed user-facing runtime layers unless the repo explicitly approves them as baked image tools

#### Scenario: Approved admin CLIs may remain baked into the image layer
- **WHEN** maintainers inspect the default-image runtime contract for operator/admin tools
- **THEN** the immutable image layer may include the repo-approved admin/debug CLI set such as `git`, `gh`, and the OpenSSH client tools
- **AND** those approved baked tools do not by themselves redefine the image as the primary home for the broader mutable user-facing tool surface
