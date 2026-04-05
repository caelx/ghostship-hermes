## 1. Dashboard Packaging

- [ ] 1.1 Ensure `packages/hermes-dashboard` builds as a first-class package artifact and explicitly ships the MMX static assets with the `hermes-dashboard` entrypoint.
- [ ] 1.2 Expose the dashboard package through the flake outputs so maintainers can build and inspect it directly outside the full image build.

## 2. Image Runtime Integration

- [ ] 2.1 Update the Hermes image runtime and NixOS module wiring so `ghostship-dashboard-controller.service` runs only through the packaged dashboard path.
- [ ] 2.2 Remove the stale legacy dashboard asset-path seam from the image runtime while preserving the environment defaults the packaged dashboard still uses.

## 3. Contract Alignment

- [ ] 3.1 Update the dashboard smoke test to validate the MMX UI contract and the packaged dashboard runtime behavior instead of the older dashboard strings.
- [ ] 3.2 Update README and any affected supporting docs to describe the packaged MMX dashboard as the canonical browser entrypoint.

## 4. Verification

- [ ] 4.1 Build the dashboard package and the Hermes image with the updated packaging/runtime path.
- [ ] 4.2 Run the dashboard image smoke test and confirm the packaged MMX dashboard serves successfully under systemd inside the container.
