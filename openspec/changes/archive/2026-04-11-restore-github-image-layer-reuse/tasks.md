## 1. GitHub Publish Path

- [x] 1.1 Restore the GitHub content-image assembly and immutable content hash to the base-plus-overlay path.
- [x] 1.2 Make the GitHub content build explicitly pull and build from the reusable `BASE_REF` tag before publishing the final image.

## 2. Specs And Docs

- [x] 2.1 Update OpenSpec publication/reuse/optimization specs to describe the layered GitHub publish path and the separate explicit local bundle contract.
- [x] 2.2 Update the README, changelog, and durable repo guidance to explain the corrected GitHub optimization contract.

## 3. Verification

- [x] 3.1 Run targeted static checks for the workflow and the updated OpenSpec artifacts.
