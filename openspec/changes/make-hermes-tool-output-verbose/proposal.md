## Why

The image currently scaffolds Hermes with relatively terse tool output defaults, which makes it harder for operators and agents to inspect full command previews and detailed tool progress during interactive sessions. We want the managed runtime to default to a more transparent CLI experience without changing the existing gateway streaming behavior.

## What Changes

- Change the managed Hermes display defaults in the image scaffold from terse progress updates to verbose tool progress.
- Add managed defaults for unlimited tool-call preview length and CLI token streaming.
- Preserve the existing non-compact display setting and existing top-level gateway streaming behavior.
- Update operator-facing documentation so the declared defaults match the runtime contract.

## Capabilities

### New Capabilities
- `hermes-display-defaults`: Defines the managed default Hermes display and CLI streaming settings that the image scaffolds for interactive sessions.

### Modified Capabilities

## Impact

- Affects the managed Hermes profile config generated from `packages/hermes-image/nixos-module.nix`.
- Affects operator-facing documentation in `README.md`, `docs/nix-setup.md`, and release notes if the defaults are documented there.
- Changes the default interactive CLI experience for the scaffolded `assistant`, `operations`, and `supervisor` profiles.
