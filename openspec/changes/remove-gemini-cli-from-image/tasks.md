## 1. Remove Gemini CLI from the managed image toolchain

- [x] 1.1 Remove `@google/gemini-cli` from the managed npm package list in `packages/hermes-image/nixos-module.nix`
- [x] 1.2 Remove the managed `gemini` bin from the runtime PATH contract in `packages/hermes-image/nixos-module.nix`

## 2. Update the live runtime contract and docs

- [x] 2.1 Update current repo docs that list installed managed CLIs so they no longer advertise Gemini CLI as installed
- [x] 2.2 Update current AGENTS guidance and any other live contract text so Gemini remains documented only as an auxiliary provider path where that is still true
- [x] 2.3 Apply the runtime and seeding spec deltas so the live OpenSpec contract no longer includes Gemini CLI as a managed installed tool

## 3. Verify the narrowed scope

- [x] 3.1 Verify current tracked code and docs no longer describe Gemini CLI as part of the managed image toolchain
- [x] 3.2 Verify current tracked Gemini references that remain are limited to the intentional Gemini API-backed auxiliary-task usage or historical archived material left out of scope
