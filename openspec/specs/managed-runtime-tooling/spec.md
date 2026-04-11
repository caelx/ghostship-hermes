## ADDED Requirements

### Requirement: Managed Hermes runtime exposes the approved helper CLI set
The workstation SHALL expose the repo-approved mutable helper CLI set through the managed Hermes user Nix profile so operators and Hermes sessions can rely on those commands without expanding the immutable image layer.

#### Scenario: Managed helper CLIs resolve from the Hermes-user PATH
- **WHEN** the container boots or the managed user-tooling refresh converges the Hermes runtime profile
- **THEN** the Hermes-user PATH exposes `fd`, `uv`, `yq`, and `tmux` from the dedicated managed Nix profile
- **AND** those commands are available to Hermes and interactive shells without an additional manual installation step

### Requirement: Managed Hermes runtime exposes a pip-capable Python environment
The workstation SHALL expose a managed Python runtime for Hermes that provides a consistent interpreter and pip workflow from the managed user profile.

#### Scenario: Python and pip commands both work from the managed runtime
- **WHEN** an operator or Hermes session invokes `python3`, `pip`, or `python3 -m pip` from the managed Hermes-user PATH
- **THEN** `python3` launches the managed interpreter
- **AND** `pip` launches successfully from the same managed runtime contract
- **AND** `python3 -m pip` also launches successfully without requiring a separate environment activation step

#### Scenario: Managed Python contract survives image replacement
- **WHEN** the workstation boots after image replacement while `/home/hermes` persists
- **THEN** the managed user-tooling convergence restores the current approved Python-and-pip runtime contract into the dedicated managed profile
- **AND** stale managed entries do not leave Hermes with a mismatched `python3` and `pip` combination
