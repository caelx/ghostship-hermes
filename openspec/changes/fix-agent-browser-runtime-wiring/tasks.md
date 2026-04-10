## 1. Runtime Wiring

- [ ] 1.1 Remove `agent-browser` from the mutable npm-managed package/bin sets in the Hermes user-tooling convergence logic.
- [ ] 1.2 Update convergence so stale `/home/hermes/.local/bin/agent-browser` links that point into the mutable npm project are removed or replaced with the supported runtime path.
- [ ] 1.3 Verify the managed runtime still exposes a working `agent-browser` command on PATH and keeps Hermes local browser mode anchored on `agent-browser`.

## 2. Validation

- [ ] 2.1 Extend the Hermes image validation suite to execute `agent-browser --help` instead of only checking `command -v agent-browser`.
- [ ] 2.2 Add or update validation for `hermes doctor` so the supported browser path does not regress after the runtime wiring change.
- [ ] 2.3 Run the relevant image/runtime checks and confirm the fix on the target architecture.

## 3. Documentation

- [ ] 3.1 Update affected runtime documentation to describe `agent-browser` as the default local browser backend delivered through the supported image/runtime path rather than the mutable npm layer.
- [ ] 3.2 Update `CHANGELOG.md` with the `agent-browser` runtime wiring fix once implementation is complete.
