## 1. Baseline And Measurement

- [x] 1.1 Capture current GitHub Actions timing baselines for `ci` and `publish-image`, including major job-level timings for both architectures
- [x] 1.2 Add repo-owned measurement notes or helper tooling so each optimization round records comparable before/after timing evidence
- [x] 1.3 Define the acceptance metrics for the optimization effort, including the approximately 10-minute publish stretch goal and the distinction between cold-cache and warm-cache runs

## 2. Round 1: Publish Gating

- [x] 2.1 Implement conservative image-affecting path detection or equivalent workflow gating for automatic `publish-image` runs
- [x] 2.2 Preserve `workflow_dispatch` and release-driven publication behavior while verifying that non-image pushes skip publication safely
- [x] 2.3 Measure the effect of publish gating on total publish frequency and end-to-end runner time consumption

## 3. Round 2: Cache-Backed Reuse

- [x] 3.1 Add a supported Nix binary cache or substituter strategy for GitHub Actions builds and document cache invalidation expectations
- [x] 3.2 Add caching or an equivalent reuse strategy for the Python utility test environment used by `ci`
- [x] 3.3 Re-measure `ci` and `publish-image` under cold-cache and warm-cache conditions and compare against the baseline

## 4. Round 3: Reuse Logic And Architecture

- [x] 4.1 Evaluate the remaining bottlenecks after gating and cache-backed reuse and identify whether the publish path still materially exceeds the target
- [x] 4.2 Prototype and select an architectural image build or publish change if it offers a defensible speedup while preserving the explicit image contract
- [x] 4.3 Implement the selected architectural change and verify multi-arch publication correctness plus runtime metadata compatibility
- [x] 4.4 Add immutable per-architecture content-tag derivation so exact-repeat publishes can reuse previously published final images
- [x] 4.5 Stabilize the reusable base-image boundary so overlay-only changes stop invalidating the base image unnecessarily
- [x] 4.6 Split the image into a true Hermes base layer and a final repo-content layer, and move approved shared dependencies into base

## 5. Boundary Verification

- [x] 5.1 Audit which shared runtimes or dependency closures are reused broadly enough to belong in the base image
- [x] 5.2 Keep repo-owned router/dashboard/runtime and utility wiring in the final image layer and verify the boundary is explicit in code
- [x] 5.3 Inspect the built `ghostship-hermes-base` closure or image contents and confirm Ghostship-owned runtime packages are absent while approved shared dependencies remain present
- [x] 5.4 Inspect the realized final overlay content against the built base image and pull any remaining shared non-Ghostship dependencies down into base until the overlay is limited to Ghostship-owned payloads plus unavoidable image-assembly metadata

## 6. Remaining Verification And Measurement

- [x] 6.1 Verify that the final `ghostship-hermes` image still satisfies the documented runtime and publication contract
- [x] 6.2 Trigger and measure an overlay-only publish on the same base content to confirm that the workflow reuses the published base image without rebuilding it
- [x] 6.3 Trigger and measure a warm-repeat publish on the same evaluated image content to confirm that the workflow retags immutable images without rebuilding them
- [x] 6.4 Compare the cold-content, base-reuse, and warm-repeat timing results and record the observed long pole, if any

## 7. Finalization

- [x] 7.1 Compare all optimization rounds and keep the fastest correct configuration
- [x] 7.2 Update repository documentation and changelog to reflect the final GitHub Actions build and publish strategy
- [x] 7.3 Record the final measured timing outcome and whether the publish path met or missed the approximately 10-minute stretch goal
