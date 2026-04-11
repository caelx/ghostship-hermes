## 1. GitHub Publish Path

- [ ] 1.1 Restore the GitHub content-image assembly and immutable content hash to the base-plus-overlay path.
- [ ] 1.2 Add a provider-independent publish-path smoke test that validates the exact built image before GHCR upload.

## 2. Specs And Docs

- [ ] 2.1 Update OpenSpec publication/reuse/optimization specs to require verification for the GitHub fast path.
- [ ] 2.2 Update the README, changelog, and durable repo guidance to explain the corrected GitHub optimization contract.

## 3. Verification

- [ ] 3.1 Run targeted checks for the workflow and the new publish-path smoke test.
