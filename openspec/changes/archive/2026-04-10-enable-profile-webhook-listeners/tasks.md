## 1. Scaffold Per-Profile Webhook Runtime

- [x] 1.1 Extend `packages/hermes-image/nixos-module.nix` profile scaffold with repo-owned webhook enablement, fixed per-profile ports, and profile-specific webhook secret source env names.
- [x] 1.2 Update the managed profile `.env` writer so `assistant`, `operations`, and `supervisor` each receive `WEBHOOK_ENABLED=true`, their assigned `WEBHOOK_PORT`, and a profile-local `WEBHOOK_SECRET` projected from the matching container env.
- [x] 1.3 Verify the gateway service contract still relies on the existing per-profile `EnvironmentFile` path rather than service-only webhook overrides.

## 2. Document The Contract

- [x] 2.1 Update `README.md` to document the fixed per-profile webhook port map and the requirement for downstream deployment config to provide `WEBHOOK_ASSISTANT_SECRET`, `WEBHOOK_OPERATIONS_SECRET`, and `WEBHOOK_SUPERVISOR_SECRET`.
- [x] 2.2 Update `CHANGELOG.md` to record the new managed per-profile webhook listener scaffold and secret env contract.

## 3. Validate The Image Scaffold

- [x] 3.1 Run targeted validation for the generated webhook env/config output so the three managed profiles receive the expected ports and secret wiring contract.
- [x] 3.2 Run the relevant repo checks for the Hermes image scaffold and record any gaps if full runtime validation is not possible in the current environment.
