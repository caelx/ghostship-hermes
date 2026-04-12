## 1. Narrow The Restart Surface

- [x] 1.1 Update the managed gateway restart path unit in `packages/hermes-image/nixos-module.nix` so it watches only `/home/hermes/.hermes/config.yaml` and `/home/hermes/.hermes/.env`.
- [x] 1.2 Verify the managed bootstrap/runtime contract still treats `auth.json` and `SOUL.md` as durable managed state without making them automatic restart triggers.

## 2. Add Stability Validation

- [x] 2.1 Extend the Hermes image validation flow to capture the running managed gateway process identity before and after mutating `auth.json`, and assert that the process does not restart.
- [x] 2.2 Extend the Hermes image validation flow to capture the running managed gateway process identity before and after mutating `SOUL.md`, and assert that the process does not restart.
- [x] 2.3 Keep or add validation that `.env` and/or `config.yaml` changes still produce restart-visible behavior for the managed gateway.

## 3. Align Docs And Change History

- [x] 3.1 Update `README.md` to describe the narrowed managed gateway restart surface and the non-restarting role of `auth.json` and `SOUL.md`.
- [x] 3.2 Update `CHANGELOG.md` to record the restart-stability fix and the removal of avoidable restarts on OAuth/prompt state changes.
- [x] 3.3 Run the relevant OpenSpec validation/status checks and confirm the change is ready for `/opsx:apply`.
