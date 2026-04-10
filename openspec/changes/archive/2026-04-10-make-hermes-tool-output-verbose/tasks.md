## 1. Update Managed Defaults

- [x] 1.1 Change the shared Hermes `display` defaults in `packages/hermes-image/nixos-module.nix` to set `tool_progress = "verbose"`.
- [x] 1.2 Add `display.tool_preview_length = 0` and `display.streaming = true` to the shared managed profile scaffold while keeping `display.compact = false` and the existing top-level `streaming` block intact.

## 2. Align Documentation

- [x] 2.1 Update `README.md` to describe the new managed display defaults and distinguish CLI display streaming from top-level gateway streaming.
- [x] 2.2 Update `docs/nix-setup.md` so the documented Hermes display keys include the verbose progress and preview/streaming defaults relevant to this repo.
- [x] 2.3 Update `CHANGELOG.md` with the new managed Hermes display defaults if the release notes track those scaffold settings.

## 3. Verify The Change

- [x] 3.1 Inspect the generated diff to confirm the managed defaults and docs all describe the same runtime contract.
- [x] 3.2 Run the appropriate repo validation for the touched docs and Nix module surface, or document any verification limits if full validation is deferred.
