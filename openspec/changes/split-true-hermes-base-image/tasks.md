## 1. Base/Final Architecture Split

- [x] 1.1 Identify the current responsibilities in `packages/hermes-image/nixos-module.nix` and separate true base concerns from final-image-only repo wiring
- [x] 1.2 Introduce distinct base and final image composition paths in the flake/module layout instead of reusing one module with shim binaries
- [x] 1.3 Remove shim binaries from the base path and ensure repo-owned commands are only introduced in the final image layer

## 2. Dependency Boundary

- [x] 2.1 Audit which shared runtimes or dependency closures are reused broadly enough to belong in the base image
- [x] 2.2 Move the approved stable shared dependencies into the base layer without reintroducing repo-owned service semantics
- [x] 2.3 Keep repo-owned router/dashboard/runtime and utility wiring in the final image layer and verify the boundary is explicit in code

## 3. Publish And Validation

- [x] 3.1 Update the publish path to build and reuse the true base image plus final repo-content layer
- [ ] 3.2 Verify that the final `ghostship-hermes` image still satisfies the documented runtime and publication contract
- [ ] 3.3 Measure whether the new base boundary reduces rebuild work for overlay-only changes
- [x] 3.4 Inspect the built `ghostship-hermes-base` closure or image contents and confirm Ghostship-owned runtime packages are absent while approved shared dependencies remain present
- [x] 3.5 Inspect the realized final overlay content against the built base image and pull any remaining shared non-Ghostship dependencies down into base until the overlay is limited to Ghostship-owned payloads plus unavoidable image-assembly metadata

## 4. Documentation

- [x] 4.1 Update `README.md`, `docs/github-actions-build-optimization.md`, `CHANGELOG.md`, and `AGENTS.md` to describe the true base/final split
- [x] 4.2 Record which dependencies are intentionally carried by the base layer and why
- [x] 4.3 Document the dependency-audit rule: when the overlay still carries shared dependencies used by Ghostship content, move them into base unless doing so would make the base churn with repo-owned changes
