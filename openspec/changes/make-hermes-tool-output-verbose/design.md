## Context

The managed Hermes image currently declares a small `display` block in the NixOS module, with `compact = false`, `tool_progress = "new"`, and `background_process_notifications = "result"`. The image also enables top-level gateway streaming separately through the `streaming` block. Upstream Hermes exposes additional display-level controls, including `tool_preview_length` and `display.streaming`, and those are the settings needed to make interactive tool output more verbose without changing the gateway transport contract.

## Goals / Non-Goals

**Goals:**
- Make scaffolded interactive Hermes sessions default to verbose tool progress.
- Keep full tool previews visible by default.
- Enable CLI display streaming in the managed profile config.
- Keep the current gateway streaming contract intact.
- Bring repo documentation into sync with the managed defaults.

**Non-Goals:**
- Changing model, reasoning, or approval defaults.
- Changing messaging-platform-specific progress overrides.
- Changing the top-level gateway `streaming.transport`, `edit_interval`, or `buffer_threshold` settings.
- Introducing per-profile divergence between `assistant`, `operations`, and `supervisor`.

## Decisions

### Set the new defaults in the shared image scaffold
The change should update the shared `display` attrset in `packages/hermes-image/nixos-module.nix` so all managed profiles inherit the same defaults. This matches the repo's existing pattern for shared Hermes profile defaults and avoids drift between profiles.

Alternative considered: documenting a manual runtime override only. Rejected because the request is to make the managed tool outputs verbose by default, not merely document an optional post-boot tweak.

### Treat CLI display streaming and gateway streaming as separate controls
The change should add `display.streaming = true` while leaving the existing top-level `streaming` block untouched. Upstream Hermes treats these as distinct controls: `display.streaming` affects CLI token display, while the top-level `streaming` block governs progressive gateway edits. Keeping both avoids conflating two different behaviors.

Alternative considered: moving all streaming behavior into the `display` block. Rejected because it would silently change the runtime meaning of the existing gateway streaming contract and could regress messaging behavior.

### Document the runtime contract where operators already look
The change should update `README.md`, `docs/nix-setup.md`, and `CHANGELOG.md` if they mention the scaffolded defaults. This keeps the declared profile scaffold and runtime behavior aligned and reduces operator confusion when inspecting live config.

Alternative considered: limiting the change to Nix only. Rejected because this repo explicitly treats README, support docs, and changelog accuracy as part of completion hygiene.

## Risks / Trade-offs

- [Verbose tool progress is noisier than the current default] → Mitigate by keeping the change limited to the managed default; operators can still override `display.tool_progress` later in their own config.
- [CLI display streaming could be mistaken for the existing gateway streaming contract] → Mitigate by documenting that `display.streaming` and top-level `streaming.enabled` control different Hermes surfaces.
- [Repo docs may lag the code change if not updated together] → Mitigate by treating the documentation edits as first-class implementation tasks in the same change.
