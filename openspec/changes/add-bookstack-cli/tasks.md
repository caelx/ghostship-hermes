## 1. Capture And Normalize The BookStack Contract

- [ ] 1.1 Pull the current official BookStack API docs into committed repo artifacts under `docs/api/` and record the capture source/version in the BookStack reference sheet.
- [ ] 1.2 Decide whether the upstream docs expose a stable machine-readable export; if not, create and commit a repo-owned normalized snapshot derived from the verified docs surface.
- [ ] 1.3 Build the BookStack operation inventory from the committed docs snapshot and verify that it covers the verified endpoint groups and binary/upload operations.

## 2. Extend The Shared CLI Transport Surface

- [ ] 2.1 Add additive shared CLI-contract support for multipart form fields and file inputs in generic full-surface utility commands and dry-run rendering.
- [ ] 2.2 Add additive shared client/CLI support for successful non-JSON or binary responses while preserving JSON-first output semantics for command results.
- [ ] 2.3 Add or update shared tests to prove existing JSON-oriented utilities continue working unchanged after the multipart/binary transport extensions.

## 3. Implement The BookStack Utility Package

- [ ] 3.1 Scaffold `packages/bookstack-cli` with `pyproject.toml`, `package.nix`, README, source package layout, and test layout matching the repo utility standard.
- [ ] 3.2 Implement the BookStack client, auth handling, and operation catalog so every verified upstream operation has a matching client method and dry-run builder.
- [ ] 3.3 Implement the `ghostship-bookstack` CLI with per-operation commands, generic request support, timeout handling, dry-run behavior, and binary/upload command semantics aligned with the shared contract changes.

## 4. Validate And Document The Utility

- [ ] 4.1 Add client and CLI tests covering auth, catalog registration, multipart upload builders, and binary endpoint handling.
- [ ] 4.2 Run the standard Python utility lock/test/build workflow for `packages/bookstack-cli` and fix any packaging or contract issues that surface.
- [ ] 4.3 Update the relevant top-level or package-level documentation so operators know how to configure and use `ghostship-bookstack`.
