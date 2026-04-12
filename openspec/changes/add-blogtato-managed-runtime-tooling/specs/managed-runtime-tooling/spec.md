## MODIFIED Requirements

### Requirement: Managed Hermes runtime exposes the approved helper CLI set
The workstation SHALL expose the repo-approved mutable helper CLI set through the managed Hermes user Nix profile so operators and Hermes sessions can rely on those commands without expanding the immutable image layer.

#### Scenario: Managed helper CLIs resolve from the Hermes-user PATH
- **WHEN** the container boots or the managed user-tooling refresh converges the Hermes runtime profile
- **THEN** the Hermes-user PATH exposes `fd`, `uv`, `yq`, `tmux`, and `blog` from the dedicated managed Nix profile
- **AND** those commands are available to Hermes and interactive shells without an additional manual installation step
