## 1. Wire The CLI Into The Image

- [x] 1.1 Add `pkgs.google-cloud-sdk` to the repo package wiring that feeds the default Hermes image utility set
- [x] 1.2 Ensure the default Hermes image exposes `gcloud` on `PATH` through the existing runtime package-set flow
- [x] 1.3 Keep the package wiring valid for both supported publish architectures

## 2. Align Policy And Docs

- [x] 2.1 Update `AGENTS.md` to include `gcloud` in the approved non-`ghostship-*` extra CLI set
- [x] 2.2 Update `README.md` and `CHANGELOG.md` to describe `gcloud` as a preinstalled default-image CLI

## 3. Verify The Runtime Contract

- [x] 3.1 Verify the repo flake evaluates the `gcloud` integration for the supported image outputs
- [x] 3.2 Verify a built runtime exposes `gcloud` on `PATH` without a bootstrap-time installer step
