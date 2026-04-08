## Why

The current Hermes image is split between Nix-packaged runtime pieces and mutable operator-installed agent tooling. In practice, that leaves the container in an awkward middle state:

- Hermes expects agent-facing CLIs like Hermes itself, Codex, Gemini CLI, Opencode, and agent-browser to exist where the runtime user can update and use them naturally.
- Operators are manually fixing auth and tool installation state inside the live container.
- Hermes doctor reports avoidable warnings for capabilities we actually intend to use.
- The image still carries too many user-facing tools in the system closure instead of treating them as mutable operator state.

We want a minimum-system-viable image. The system layer should keep only what is required to boot, supervise services, and expose the dashboard/router surface. Hermes and the user-facing CLI toolchain should become updateable user-managed state, validated live first and only then backported into the repo image contract.

## What Changes

- Define a live-first rollout where the running Hermes container is the proving ground for the new runtime model.
- Shrink the image-owned system layer to the minimum viable set needed for boot, supervision, dashboard, router, and terminal hosting.
- Move updateable user-facing tools into managed user state, including Hermes itself, `git`, `curl`, `jq`, `python3`, `nix`, `ripgrep`, and `node`/`npm`.
- Keep the in-container Nix daemon/socket available so `nix profile install` and `nix profile upgrade` work for the `hermes` user at boot and during daily refreshes.
- Add a persisted npm tool prefix and a managed updater model for the fast-moving agent CLIs: `@openai/codex`, `@google/gemini-cli`, `opencode-ai`, and `agent-browser`, with `codex`, `gemini`, `opencode`, and `agent-browser` installed where Hermes expects them, configured for normal runtime use, and kept available on the runtime PATH.
- Make Hermes itself updateable through the managed user Nix profile rather than treating the image-owned Hermes package as authoritative forever.
- Include Home Assistant support by packaging or installing the dependency set Hermes expects for the `homeassistant` tool.
- Reduce Hermes doctor noise only for the features we actually intend to use, then confirm the resulting behavior with the operator before backporting the contract into this repo and pushing a new image.
- Align ttyd with the dashboard visual theme so the terminal surface no longer looks visually detached from the rest of the Hermes UI, specifically by using the same blue theme tokens as the dashboard rather than a generic terminal palette.

## Out of Scope

- Making every optional Hermes doctor warning disappear, especially for unused integrations.
- Replacing Hermes-native per-profile auth/model flows with a repo-specific abstraction.
- Keeping a broad workstation-style system package set in the immutable image.

## Impact

- The repo will move to a stronger separation:
  - minimum viable immutable system layer
  - updateable user Nix profile toolchain
  - updateable npm-managed fast-moving agent CLIs
- Hermes itself becomes updateable without waiting for a new image build.
- The pushed image will reflect a runtime contract that has already been validated live with the operator.
