## 1. Image integration

- [x] 1.1 Add the official `bitwarden-cli` package to the repo's image wiring so `bw` is available directly on `PATH` in the Hermes container.
- [x] 1.2 Verify the new Bitwarden CLI package is covered by normal flake evaluation and the Hermes image output.
- [x] 1.3 Decide and document the repo's recommended `BITWARDENCLI_APPDATA_DIR` convention for persistent local CLI state.

## 2. Skill and workflow guidance

- [x] 2.1 Add a repo-managed Bitwarden skill to `skills/` and include it in the default seeded skill tree.
- [x] 2.2 Document the supported stateless workflow using `BW_CLIENTID`, `BW_CLIENTSECRET`, `BW_PASSWORD`, `BITWARDENCLI_APPDATA_DIR`, and `BW_SESSION`.
- [x] 2.3 Document the dedicated-account and shared-collection workflow for receiving operator-shared credentials through Bitwarden.

## 3. Verification and release hygiene

- [x] 3.1 Verify `bw` is available inside the built image/runtime and the seeded Bitwarden skill appears in a fresh Hermes profile.
- [x] 3.2 Confirm the final proposal, design, specs, skill, and docs all describe the same official Bitwarden CLI workflow.
- [x] 3.3 Update changelog/versioning as warranted by the final implementation scope before release.
