## 1. Flake outputs and shared image conversion

- [x] 1.1 Add explicit flake outputs for the low-level workstation tarball and the publishable `ghostship-hermes` image artifact, with names that make their consumer boundaries clear.
- [x] 1.2 Implement a repo-owned helper or packaging path that converts the workstation tarball artifact into a publishable image artifact while preserving `/init`, environment defaults, exposed port, labels, and volume metadata.
- [x] 1.3 Update any image-output discovery logic in repo scripts to call the explicit output/helper instead of inferring artifact shape from `result`.

## 2. CI and image-test consumers

- [x] 2.1 Update `.github/workflows/publish-image.yml` to build, upload, and publish the explicit publishable image artifact for each architecture.
- [x] 2.2 Update image-focused test helpers to load or import the explicit publishable image artifact through the shared conversion path instead of assuming an old `docker load` archive format.
- [x] 2.3 Keep rootfs-oriented workstation persistence validation on the explicit low-level tarball artifact and remove any ambiguity about which artifact it should consume.

## 3. Documentation and contract alignment

- [x] 3.1 Update `README.md` and any repo guidance that documents image builds so `ghostship-hermes-image` and the low-level tarball output have explicit, non-overlapping meanings.
- [x] 3.2 Update `CHANGELOG.md` and any affected maintainer guidance to describe the restored image artifact contract and why the output split exists.
- [x] 3.3 Verify the OpenSpec proposal, design, specs, and implementation docs all describe the same artifact names and consumer responsibilities.

## 4. Verification

- [x] 4.1 Build the explicit publishable image artifact locally and confirm it can be loaded or imported into Docker with the expected metadata intact.
- [x] 4.2 Run the image-focused local test flow against the explicit publishable artifact and confirm the dashboard/runtime path still works.
- [x] 4.3 Run the workstation persistence validation against the explicit low-level tarball artifact and confirm it still exercises the `/init`-based systemd workstation path.
