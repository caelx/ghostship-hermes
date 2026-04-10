## Why

The current managed Hermes display defaults were recently tuned for maximum inspection detail, but that profile is noisier and less compact than the operator display policy we want long term. We now want the image scaffold to default to a calmer, compact CLI presentation while keeping streamed output enabled.

## What Changes

- Replace the shared managed Hermes `display` defaults with a compact policy that sets `compact = true`, `tool_progress = "all"`, `background_process_notifications = "result"`, `bell_on_complete = false`, `show_reasoning = false`, `streaming = true`, and `skin = "default"`.
- Remove the managed `display.tool_preview_length = 0` override so the image no longer pins unlimited tool previews as part of the shared display contract.
- Preserve the existing top-level gateway streaming behavior; this change only updates the managed Hermes CLI display policy.
- Update operator-facing documentation so the declared display defaults in the repo match the managed image scaffold.

## Capabilities

### New Capabilities

### Modified Capabilities
- `hermes-display-defaults`: change the managed Hermes display requirements from verbose inspection-first defaults to the new compact shared display policy

## Impact

- Affected code: `packages/hermes-image/nixos-module.nix`
- Affected documentation: `README.md`, `docs/nix-setup.md`, `CHANGELOG.md`
- Affected system behavior: the default interactive CLI display for managed `assistant`, `operations`, and `supervisor` profiles
