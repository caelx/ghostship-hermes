## 1. Restore Gemini CLI through the managed npm tooling flow

- [x] 1.1 Add `@google/gemini-cli` to the managed npm package set and `gemini` to the projected managed npm bin set in `packages/hermes-image/nixos-module.nix`.
- [x] 1.2 Verify the existing managed `nodejs_22` dependency and `.local/bin` symlink projection continue to support Gemini CLI without expanding the immutable image package set.

## 2. Update runtime contract docs

- [x] 2.1 Update runtime documentation to describe `gemini` as a managed persisted npm CLI alongside `codex` and `opencode`.
- [x] 2.2 Keep the docs explicit that Gemini CLI remains separate from the Gemini auxiliary-provider configuration that uses `GOOGLE_AI_STUDIO_API_KEY`.

## 3. Extend validation coverage

- [x] 3.1 Update Hermes image validation or smoke coverage to execute a non-destructive `gemini` command from the Hermes-user default PATH.
- [x] 3.2 Verify the validation still reflects the supported exception model where `agent-browser` remains image-managed while `codex`, `gemini`, and `opencode` come from the managed npm tooling flow.
