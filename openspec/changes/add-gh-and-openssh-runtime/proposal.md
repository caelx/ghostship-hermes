## Why

The current image runtime already exposes several operator-facing tools, but `gh` and `openssh` are still missing from the default PATH even though they are useful for normal admin, debug, and repository workflows. Adding them now closes a practical gap in the baked image contract without reopening the broader browser/media package debate around Chromium or ffmpeg.

## What Changes

- Add the GitHub CLI (`gh`) to the default Hermes image runtime through the repo's normal Nix/image package wiring.
- Add the OpenSSH client package so `ssh` and `scp` are available on the default Hermes image PATH.
- Keep this change narrowly scoped to the image/runtime contract and associated operator documentation.
- Explicitly leave Chromium and ffmpeg out of scope for this change.

## Capabilities

### New Capabilities
- `github-and-ssh-cli-runtime`: Define the default-image contract for shipping `gh`, `ssh`, and `scp` from the repo's normal Nix/image package wiring.

### Modified Capabilities
- `agent-workstation-runtime`: Clarify that the supported immutable runtime layer may include repo-approved admin CLIs such as `gh` and `openssh` even while the broader user-facing tool surface remains managed outside the immutable layer.

## Impact

- Affected code: [packages/hermes-image/nixos-module.nix](/home/nixos/dev/ghostship-hermes/packages/hermes-image/nixos-module.nix), related flake/image wiring, and runtime verification paths.
- Affected docs: runtime policy in [AGENTS.md](/home/nixos/dev/ghostship-hermes/AGENTS.md), README or image guidance as needed, and any tests or checks that assert default image tool availability.
- Dependencies/systems: nixpkgs package wiring for `gh` and `openssh`, plus the default Hermes image contract.
