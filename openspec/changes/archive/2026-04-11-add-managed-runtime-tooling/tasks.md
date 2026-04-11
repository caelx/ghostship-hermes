## 1. Managed Tooling Wiring

- [x] 1.1 Add `fd`, `uv`, `yq-go`, and `tmux` to the managed Hermes user-tooling inventory in the Nix module.
- [x] 1.2 Define a pip-capable managed Python environment and install it through the managed user-tooling convergence path so `python3`, `pip`, and `python3 -m pip` all work from the managed profile.
- [x] 1.3 Keep the immutable image package policy unchanged unless a boot-critical validation path proves a separate exception is required.

## 2. Validation

- [x] 2.1 Add or update runtime validation to execute `fd`, `uv`, `yq`, and `tmux` from the Hermes-user PATH.
- [x] 2.2 Add or update runtime validation to execute `python3 --version`, `pip --version`, and `python3 -m pip --version` from the Hermes-user PATH.

## 3. Documentation

- [x] 3.1 Update README to document the expanded managed user-tool inventory and the pip-capable Python contract.
- [x] 3.2 Update `docs/nix-setup.md` to replace the old “no runtime pip” guidance with the new managed Python-and-pip behavior where applicable.
