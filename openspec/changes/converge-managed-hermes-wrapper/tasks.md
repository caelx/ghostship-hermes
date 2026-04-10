## 1. Convergence Strategy

- [ ] 1.1 Decide and document which repo-owned persisted user-layer system state must converge on boot or image replacement.
- [ ] 1.2 Update the managed user tooling/bootstrap flow so the active `hermes` binary no longer stays pinned to an older persisted wrapper revision after replacement.

## 2. Runtime Alignment

- [ ] 2.1 Ensure the Hermes-user PATH continues to resolve through the managed profile while the resolved `hermes` package matches the current runtime generation.
- [ ] 2.2 Converge any other repo-managed persisted system config carried in the user layer that is supposed to track the current image/runtime contract.
- [ ] 2.3 Disable Discord auto-thread creation in the managed profile scaffold for `assistant`, `operations`, and `supervisor`.
- [ ] 2.4 Verify managed gateway status and doctor behavior use the converged wrapper path for `assistant`, `operations`, and `supervisor`.

## 3. Validation

- [ ] 3.1 Extend image/runtime validation to assert the resolved `hermes` path or wrapper generation after replacement.
- [ ] 3.2 Extend replacement validation to assert repo-managed persisted config converges to the current runtime contract after replacement.
- [ ] 3.3 Extend replacement validation to assert healthy managed gateways still report as running through `hermes -p <profile> gateway status` and `hermes -p <profile> doctor`.
- [ ] 3.4 Extend validation to assert Discord auto-threading is disabled in the managed profile config for all three profiles.

## 4. Documentation

- [ ] 4.1 Update runtime/operator documentation to explain how repo-owned persisted system config converges across image replacement.
- [ ] 4.2 Document the managed Discord default change so operators know automatic thread creation is now disabled for the profile gateways.
