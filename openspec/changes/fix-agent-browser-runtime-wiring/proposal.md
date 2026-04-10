## Why

The current image advertises `agent-browser` as the default local browser backend for Hermes, but the live arm64 container wires `/home/hermes/.local/bin/agent-browser` to a raw npm-installed shim whose native backend fails to launch with `ENOENT`. This leaves the documented default broken in practice even though the image already ships a working Nix-packaged `agent-browser`.

## What Changes

- Stop managing `agent-browser` through the mutable npm tooling layer under `/home/hermes/.hermes/hermes-agent`.
- Keep `agent-browser` available on the Hermes runtime PATH through the image-managed Nix package and make the operator-facing `agent-browser` command resolve to that working binary.
- Preserve Hermes' local browser default so profile browser workflows and the browser skill continue using `agent-browser`.
- Keep `hermes doctor` satisfied by the supported runtime wiring after the mutable npm exception is removed.
- Extend image validation so `agent-browser --help` is executed during runtime tests instead of only checking command discovery.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `agent-workstation-runtime`: The managed runtime command contract must guarantee that invoking `agent-browser` launches a working backend on supported image architectures while keeping Hermes' default local browser path intact.
- `agent-workstation-updates`: The managed user-tooling refresh contract must allow repo-managed exceptions where a supported CLI is kept on PATH from the image/runtime layer instead of being installed from the mutable npm layer, and validation must exercise the command rather than only checking `command -v`.

## Impact

- Affected code: [packages/hermes-image/nixos-module.nix](/home/nixos/dev/ghostship-hermes/packages/hermes-image/nixos-module.nix), [tests/hermes-image/profiles-dashboard.sh](/home/nixos/dev/ghostship-hermes/tests/hermes-image/profiles-dashboard.sh), and any related runtime docs or changelog entries updated during implementation.
- Affected systems: Hermes runtime tooling convergence, Hermes local browser workflows, `hermes doctor`, and arm64 live-image validation.
- Dependencies: Existing Nix-packaged `agent-browser` output and the wrapped Hermes doctor/runtime shims already present in the image.
