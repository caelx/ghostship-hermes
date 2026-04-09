## 1. Runtime PATH Contract

- [ ] 1.1 Update the Hermes image runtime contract so `/home/hermes/.local/bin` is part of the Hermes user's default command-discovery PATH where supported user-facing Hermes invocations run.
- [ ] 1.2 Verify that `codex`, `gemini`, `opencode`, and `agent-browser` remain discoverable through the intended Hermes-user PATH contract after boot and managed tooling refresh.

## 2. Profile Env Projection

- [ ] 2.1 Extend the bootstrap env pass-through contract to include the documented shared and per-profile Discord variables needed for profile `.env` generation.
- [ ] 2.2 Keep the generated managed profile `.env` files as the single operator-facing source of truth for supported profile-facing runtime env, including the projected Hermes-facing Discord keys.
- [ ] 2.3 Verify that regenerated profile `.env` files contain the supported projected keys when those values are present on the container and omit them when they are absent.

## 3. Validation And Documentation

- [ ] 3.1 Update operator-facing docs to describe the Hermes-user PATH contract and the supported profile `.env` projection contract.
- [ ] 3.2 Extend validation or smoke coverage so the change checks the intended PATH/discovery behavior and the profile `.env` projection behavior for supported runtime inputs.
- [ ] 3.3 Re-run the relevant Hermes runtime checks to confirm the supported `codex` and messaging-path warnings are reduced for correctly configured profiles.
