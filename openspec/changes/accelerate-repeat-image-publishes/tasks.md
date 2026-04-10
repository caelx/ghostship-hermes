## 1. Workflow Reuse Logic

- [ ] 1.1 Add or refine immutable per-architecture content-tag derivation in `.github/workflows/publish-image.yml` so it reflects both the base-image and overlay-bundle derivations
- [ ] 1.2 Check GHCR for the immutable content-addressed final image before starting rebuild work and reuse it when present
- [ ] 1.3 Keep the reusable base-image path as the fallback when the immutable final image does not exist yet

## 2. Verification And Measurement

- [ ] 2.1 Verify that a cold-content publish still builds and publishes both architectures correctly plus the final manifest list
- [ ] 2.2 Trigger and measure a warm-repeat publish on the same evaluated image content to confirm that the workflow retags the immutable images without rebuilding them
- [ ] 2.3 Compare the cold-content and warm-repeat timing results and record the observed long pole, if any

## 3. Documentation

- [ ] 3.1 Update `README.md`, `docs/github-actions-build-optimization.md`, and `CHANGELOG.md` to describe the repeat-publish reuse order and the free-only rationale
- [ ] 3.2 Record the final timing evidence and note whether the warm-repeat publish path materially reduces latency even if the cold-content path remains slow
