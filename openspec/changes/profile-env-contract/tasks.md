## 1. Contract Inventory

- [ ] 1.1 Define the approved shared profile-facing env allowlist for managed profile `.env`
- [ ] 1.2 Define the approved profile-scoped translation table for Discord, webhook secrets, and per-profile browser CDP env
- [ ] 1.3 Define the explicit container-only exclusion list, including router-daemon and image-plumbing env

## 2. Bootstrap Wiring

- [ ] 2.1 Update the bootstrap `PassEnvironment` contract so every supported profile-facing env input is visible to the `.env` writer
- [ ] 2.2 Update `write_profile_env()` to emit the full shared allowlist and the approved profile-scoped translations
- [ ] 2.3 Add per-profile browser CDP source env mapping: `BROWSER_ASSISTANT_CDP_URL`, `BROWSER_OPERATIONS_CDP_URL`, and `BROWSER_SUPERVISOR_CDP_URL` to profile-local `BROWSER_CDP_URL`
- [ ] 2.4 Keep router-daemon variables out of managed profile `.env`
- [ ] 2.5 Preserve idempotent `.env` writes so unchanged effective content does not rewrite the file

## 3. Docs And Validation

- [ ] 3.1 Update repo guidance and operator docs to describe the full managed profile `.env` contract and the profile-scoped browser CDP variable names
- [ ] 3.2 Add or update validation coverage to assert the expected profile `.env` contents and exclusions
- [ ] 3.3 Verify that supported env changes rewrite only the affected profile `.env` and that unchanged boot does not trigger avoidable restarts
