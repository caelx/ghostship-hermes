## 1. Managed Runtime Identity

- [x] 1.1 Update the Hermes bootstrap/runtime scaffolding to materialize managed markers for each managed profile home as well as the root Hermes home
- [x] 1.2 Verify the managed runtime environment and profile wrappers expose the intended managed-state contract for interactive `hermes` invocations

## 2. Gateway Command Alignment

- [x] 2.1 Patch the wrapped Hermes gateway CLI so managed profile `gateway status` resolves the repo-owned `ghostship-hermes-profile-*` services instead of upstream `hermes-gateway*` units
- [x] 2.2 Patch managed gateway control-path behavior (`start`, `stop`, `restart`, and root-level status guidance) so the CLI either targets the correct managed service or exits with explicit managed-runtime guidance
- [x] 2.3 Verify `hermes doctor` and related health output no longer report false stopped gateways for healthy managed profiles

## 3. Validation And Documentation

- [x] 3.1 Add or update image/runtime validation to cover `hermes -p <profile> doctor` and `hermes -p <profile> gateway status` for the managed profiles
- [x] 3.2 Add a managed control-path validation case for at least one gateway mutation command or managed guidance path
- [x] 3.3 Update operator-facing docs to explain the managed gateway command behavior inside the image and the repo-owned service topology
