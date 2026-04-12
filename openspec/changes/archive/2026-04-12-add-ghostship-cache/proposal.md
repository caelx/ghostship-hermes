## Why

`publish-image` is back on unconditional full native builds because the free GHCR image-layer reuse and the later daily-image in-container experiment did not materially speed the Nix portion of the build and repeatedly failed on raw-image runtime mismatches. A real free Nix reuse path needs to cache store paths, not Docker layers, and the new `caelx/ghostship-cache` repository gives Ghostship a dedicated place to do that across multiple Nix projects.

## What Changes

- Introduce a shared Ghostship Nix binary cache contract centered on the dedicated `caelx/ghostship-cache` repository, backed by `nixcache-oci` and GHCR instead of repo-specific OCI parent-image tricks.
- Integrate `ghostship-hermes` phase 1 consumption and publication of that cache in the GitHub `publish-image` workflow through a runner-local proxy/substituter path while preserving the explicit `ghostship-hermes-image` publication contract.
- Require a signed shared-cache trust model for Ghostship repos instead of unsigned global cache disablement.
- Keep publication reliable by falling back to the current full host-side build when the shared cache is empty or unavailable, rather than introducing another alternate image-assembly architecture.
- Document the shared cache repo role, publisher policy, signing/secret handling, and measurement plan so other Ghostship Nix repos can adopt the same cache later.

## Capabilities

### New Capabilities
- `shared-nix-binary-cache`: Defines the shared `caelx/ghostship-cache` GHCR-backed Nix cache, the trust model, and the multi-repo consumer/publisher contract.

### Modified Capabilities
- `image-publication-contract`: Allow `publish-image` to consume and publish supported Nix build outputs through the shared Ghostship binary cache while keeping the explicit `ghostship-hermes-image` bundle and normal full-build fallback contract.

## Impact

- Affected repos: `ghostship-hermes` and the new infrastructure repo `ghostship-cache`.
- Affected systems: GitHub Actions `publish-image`, GHCR-backed cache storage, Nix substituter configuration, signing-key handling, and cache runbooks/docs.
- Dependencies: `nixcache-oci`, GHCR repository/package permissions, a shared cache signing keypair, and repo/workflow secrets for cache publication.
