## Context

The workstation refactor intentionally moved the runtime to a NixOS `systemd` container model and changed the flake image output to `ghostshipHermesSystem.config.system.build.tarball`. That output is useful for rootfs-oriented workflows, and the newer workstation validation script already knows how to find the nested `*.tar.xz` file and import it into Docker.

The rest of the repo still assumes the older contract. GitHub Actions treats `ghostship-hermes-image` as a single file that can be copied from `result`, passed to `skopeo` as `docker-archive:`, and published directly to GHCR. The older dashboard test helper similarly expects a `docker load`-compatible image tar.

That leaves the repo with one output name and two incompatible meanings:

- a low-level NixOS tarball tree used by workstation validation
- a publishable container image archive expected by CI, GHCR publication, docs, and some tests

The fix needs to restore a single explicit contract while preserving the newer workstation runtime model.

## Goals / Non-Goals

**Goals:**
- Make image-related flake outputs explicit enough that maintainers can tell which one is for publication and which one is for rootfs-level validation.
- Preserve the current NixOS `systemd` workstation runtime as the source of truth for the container filesystem and `/init` boot behavior.
- Provide one repo-owned conversion path from the low-level workstation image artifact to a publishable container image artifact with the correct metadata.
- Update CI publishing, local image tests, and repo documentation to consume the correct output through a shared contract.
- Prevent future runtime refactors from breaking image publishing by leaving stale assumptions in scripts or workflows.

**Non-Goals:**
- Reverting the workstation runtime back to the pre-`systemd` Docker image model.
- Changing the runtime behavior of the published container beyond what is necessary to preserve the current workstation contract.
- Introducing a second independently maintained container build path that can drift from the NixOS workstation rootfs.
- Redesigning unrelated runtime, seeding, or persistence behavior.

## Decisions

### Keep the NixOS workstation tarball as the low-level source artifact

The current NixOS `system.build.tarball` output should remain the low-level artifact for rootfs-oriented validation because it matches the `systemd` workstation model and already powers the newer persistence validation.

Alternative considered: discard the NixOS tarball flow and revert `ghostship-hermes-image` to the old `dockerTools.buildImage` path. Rejected because that would walk back the explicit `systemd` workstation model instead of aligning the repo around it.

### Restore `ghostship-hermes-image` as the publishable image contract and name the tarball output separately

The repo should stop overloading one output name for two artifact types. The flake should expose a clearly named low-level tarball output for workstation import flows, and `ghostship-hermes-image` should resolve to the publishable image artifact that downstream CI, GHCR publication, docs, and image tests expect.

Alternative considered: keep `ghostship-hermes-image` as the tarball tree and update every downstream consumer to handle it. Rejected because the repo documentation and public image contract already frame `ghostship-hermes-image` as the image maintainers build and publish, not an implementation detail of the NixOS layer.

### Use one repo-owned conversion path to apply container metadata

The publication path should derive the publishable image from the low-level workstation artifact through a single repo-owned helper, rather than re-embedding artifact-discovery logic in every workflow or test script. That helper should be responsible for:

- locating the low-level tarball payload
- importing or packaging it into a publishable image
- applying the expected runtime metadata such as entrypoint, default command, environment, exposed port, labels, and volume declarations

Alternative considered: keep separate ad hoc conversion snippets in CI and tests. Rejected because duplication is what allowed the contracts to drift in the first place.

### Route each consumer to the explicit artifact it actually needs

Each downstream path should consume the explicit output that matches its job:

- GHCR publication consumes the publishable image artifact
- dashboard/image smoke tests consume the publishable image artifact
- workstation rootfs/persistence validation consumes the low-level tarball output

Alternative considered: force every consumer through the publishable image artifact. Rejected because the rootfs-oriented persistence validation is deliberately lower-level and already exercises the `/init`-based workstation import path directly.

### Keep docs and validation aligned with the output names

The repo docs, validation guidance, and change log should describe the explicit output names and their intended consumers so future maintainers do not infer semantics from historical scripts.

Alternative considered: rely on implementation details and comments inside workflows. Rejected because the mismatch already reached user-facing docs and repo scripts.

## Risks / Trade-offs

- [Two related outputs can still confuse maintainers] -> Use explicit names, document the intended consumer for each output, and keep `ghostship-hermes-image` reserved for the publishable image contract.
- [Metadata reconstruction could drift from the actual workstation runtime] -> Centralize conversion logic in one helper and verify published/test-loaded images preserve `/init`, environment defaults, labels, and exposed port behavior.
- [CI and local validation may diverge again if scripts bypass the shared helper] -> Route all image-loading and publishing flows through the same repo-owned conversion path.
- [Changing output names can break existing local maintainer habits] -> Update README guidance and keep the public `ghostship-hermes-image` selector aligned with the documented build command.

## Migration Plan

1. Introduce explicit flake outputs for the low-level workstation tarball and the publishable image artifact.
2. Add a shared repo helper that converts the low-level workstation artifact into a publishable image with the required metadata.
3. Update `publish-image.yml` to build and publish from the explicit publishable image artifact.
4. Update image-focused test helpers to load or import the explicit publishable image artifact through the shared helper path.
5. Keep persistence validation on the explicit low-level workstation tarball output.
6. Update docs and changelog entries so the build, test, and publish instructions match the new artifact names and consumer boundaries.

## Open Questions

- Should the shared conversion helper emit a Docker archive, OCI archive, or both for local and CI consumers?
- Which output names are clearest for the low-level workstation tarball versus the publishable image artifact while preserving existing maintainer expectations?
