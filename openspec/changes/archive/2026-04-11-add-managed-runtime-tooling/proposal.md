## Why

The managed Hermes user profile is now the repo-approved home for broadly updateable operator tooling, but it still omits several day-to-day tools that maintainers already expect in the dev shell and runtime docs. Python is also only partially represented today: the docs mention `python3` in the managed profile, while the actual runtime does not expose a pip-capable managed Python toolchain.

This change is needed now so the managed runtime contract matches the documented operator workflow and gives Hermes a complete mutable tool layer for file discovery, YAML processing, Python packaging, terminal multiplexing, and repo-local Python utility work without expanding the immutable image unnecessarily.

## What Changes

- Add `fd`, `uv`, `yq-go`, and `tmux` to the managed Hermes user tooling contract so they are converged into the dedicated managed Nix profile on boot and refresh.
- Add a pip-capable managed Python runtime for Hermes so `python3`, `pip`, and `python3 -m pip` all work from the managed user profile.
- Define the managed runtime-tooling inventory explicitly instead of relying on partial README lists or dev-shell-only expectations.
- Update runtime docs and validation guidance so the mutable Hermes-user toolchain contract matches the actual managed profile behavior.
- Keep these tools in the managed user layer rather than widening the immutable default-image CLI policy.

## Capabilities

### New Capabilities
- `managed-runtime-tooling`: Defines the managed Hermes-user tool inventory, including the pip-capable Python runtime and operator-facing helper CLIs that must be available from the managed Nix profile.

### Modified Capabilities
- `agent-workstation-runtime`: Clarify that the managed Hermes-user runtime surface includes a pip-capable Python toolchain and the expanded mutable operator tooling set through the managed user profile rather than the immutable image.

## Impact

- Affected code: [packages/hermes-image/nixos-module.nix](/home/nixos/dev/personal/ghostship-hermes/packages/hermes-image/nixos-module.nix), [flake.nix](/home/nixos/dev/personal/ghostship-hermes/flake.nix), runtime validation scripts, and related docs.
- Affected runtime systems: managed user-tooling convergence, Hermes-user PATH behavior, mutable Python tooling, and operator CLI workflows inside the container.
- Affected docs and specs: README, [docs/nix-setup.md](/home/nixos/dev/personal/ghostship-hermes/docs/nix-setup.md), `agent-workstation-runtime`, and the new `managed-runtime-tooling` capability.
