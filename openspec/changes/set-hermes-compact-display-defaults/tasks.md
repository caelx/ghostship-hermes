## 1. Managed Display Defaults

- [ ] 1.1 Update the shared Hermes `display` block in `packages/hermes-image/nixos-module.nix` to match the compact managed policy (`compact = true`, `tool_progress = "all"`, `background_process_notifications = "result"`, `bell_on_complete = false`, `show_reasoning = false`, `streaming = true`, `skin = "default"`).
- [ ] 1.2 Remove the managed `display.tool_preview_length = 0` override from the shared display scaffold.
- [ ] 1.3 Verify the shared top-level `streaming` block remains unchanged so gateway streaming behavior stays separate from CLI display streaming.

## 2. Documentation And Spec Alignment

- [ ] 2.1 Update `README.md` to describe the new managed Hermes display defaults and the removal of the explicit unlimited tool-preview default.
- [ ] 2.2 Update `docs/nix-setup.md` so the documented display keys and explanation match the new compact managed policy.
- [ ] 2.3 Update `CHANGELOG.md` to record the managed Hermes display-policy reset.

## 3. Verification

- [ ] 3.1 Review the generated managed Hermes profile config path or rendered Nix configuration to confirm the new `display.*` values are present for managed profiles.
- [ ] 3.2 Verify the repo no longer declares `display.tool_preview_length = 0` as part of the shared managed display defaults.
