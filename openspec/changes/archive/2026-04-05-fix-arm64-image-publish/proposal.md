## Why

The image publish workflow on `main` currently tries to build the `aarch64-linux` image on an `x86_64-linux` runner. That path cannot execute native `aarch64-linux` Nix derivations, so the multi-arch release pipeline is structurally broken even when the image code itself is healthy.

## What Changes

- Update image publication jobs so each architecture builds on a runner or builder environment that can execute that target system's Nix derivations.
- Keep the existing explicit `ghostship-hermes-image` artifact contract and publish stage, but make publication depend on two successful per-architecture build artifacts.
- Distinguish x86-host arm64 evaluation from full arm64 artifact production so x86-only validation paths do not attempt unsupported full arm64 image builds.
- Update maintainer guidance and release documentation to match the repo rule that full arm64 builds require arm64 infrastructure.

## Capabilities

### New Capabilities

### Modified Capabilities

- `image-publication-contract`: Tighten the multi-arch publication contract so architecture-specific image builds run on executable target environments and x86-only validation stays at arm64 evaluation unless an arm64 builder is available.

## Impact

- Affected code: `.github/workflows/publish-image.yml`, `.github/workflows/ci.yml`, and any image-build helper logic that assumes x86 runners can build arm64 outputs.
- Affected systems: GitHub Actions image publication, release artifact generation, and maintainer validation guidance for arm64 builds.
- Affected runtime contract: `main` publishes multi-arch image tags only after both amd64 and arm64 publishable image artifacts are built in executable target environments.
