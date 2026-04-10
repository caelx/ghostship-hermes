## Context

The managed Hermes image currently scaffolds all three declared profiles with an inspection-heavy display policy: non-compact layout, verbose tool progress, explicit unlimited tool previews, and CLI streaming enabled. That profile was useful for surfacing tool details, but it is not the display contract we now want as the repo default.

This repo already centralizes shared Hermes display defaults in one `display` attrset inside `packages/hermes-image/nixos-module.nix`, and the existing `hermes-display-defaults` spec documents those requirements. The requested change is a policy reset within that same shared scaffold rather than a dashboard redesign or a broader model/runtime change.

## Goals / Non-Goals

**Goals:**
- Replace the shared managed Hermes display defaults with the new compact display policy.
- Keep the change localized to the shared `display` block so all managed profiles remain aligned.
- Preserve CLI token streaming and existing top-level gateway streaming behavior as separate controls.
- Update the `hermes-display-defaults` spec and repo docs so the runtime contract stays accurate.

**Non-Goals:**
- Changing the browser dashboard UI or its terminal management behavior.
- Changing model defaults, reasoning effort, approvals, or any non-display Hermes settings.
- Adding a new display capability when the existing `hermes-display-defaults` capability already covers this contract.

## Decisions

### Replace the shared display contract in one place
The change should update only the shared `display` attrset in `packages/hermes-image/nixos-module.nix` so `assistant`, `operations`, and `supervisor` continue inheriting one consistent display policy.

Alternative considered: customize each managed profile separately. Rejected because that would introduce unnecessary drift into a repo area that is already intentionally shared.

### Treat compactness and tool verbosity as policy shifts, not additive tweaks
The managed display defaults should move from `compact = false` and `tool_progress = "verbose"` to `compact = true` and `tool_progress = "all"` as an explicit shift toward calmer day-to-day operator output.

Alternative considered: change only `show_reasoning` and leave the recent verbose defaults intact. Rejected because the requested display policy is broader than reasoning visibility and intentionally changes the overall feel of the CLI.

### Drop the explicit unlimited tool preview override
The managed display block should stop declaring `tool_preview_length = 0` so the repo no longer promises unrestricted previews as part of the shared default contract.

Alternative considered: keep `tool_preview_length = 0` alongside the new compact policy. Rejected because the requested Option B display block intentionally omits that key.

### Keep CLI display streaming separate from gateway streaming
The change should keep `display.streaming = true` while leaving the existing top-level `streaming` block untouched. This preserves the existing distinction between CLI token streaming and gateway-side progressive edits.

Alternative considered: fold all streaming behavior into one setting. Rejected because upstream Hermes treats these as distinct surfaces and the repo already documents that separation.

## Risks / Trade-offs

- [Risk] Operators may lose some inspectability compared with the recent verbose defaults. → Mitigation: keep the change confined to managed defaults and document that Hermes can still override these display settings per profile later.
- [Risk] Removing the explicit `tool_preview_length = 0` override may surprise operators who became used to full previews. → Mitigation: call out the removal in the proposal, spec delta, and release/docs updates rather than treating it as incidental cleanup.
- [Risk] Future contributors may confuse the browser dashboard with the Hermes CLI display contract. → Mitigation: document clearly that this change affects managed Hermes profile config, not the browser dashboard package.
