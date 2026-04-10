## Context

The current Hermes image has two different `agent-browser` delivery paths:

- a Nix-packaged `agent-browser` binary that already works in the live arm64 image
- a mutable npm-managed `agent-browser` install under `/home/hermes/.hermes/hermes-agent/node_modules`

Today the managed user-tooling convergence script rewrites `/home/hermes/.local/bin/agent-browser` to the npm `.bin` shim inside the mutable tooling project. On arm64 that shim selects the upstream native binary from `node_modules/agent-browser/bin/agent-browser-linux-arm64`, and that binary fails to launch with `ENOENT`. The result is a broken operator-facing `agent-browser` command even though the image already ships a working Nix-managed wrapper for the same tool.

This change crosses the runtime convergence script, PATH contract, Hermes doctor expectations, and image validation. It also has to preserve the existing browser default of `browser.cloud_provider = "local"` so Hermes and the browser skill continue treating `agent-browser` as the default local backend.

## Goals / Non-Goals

**Goals:**

- Make `agent-browser` invocation succeed on the supported image architectures, including arm64.
- Keep `agent-browser` as the default local Hermes browser backend.
- Keep `hermes doctor` satisfied through the supported runtime wiring.
- Preserve the mutable npm-managed update model for the remaining fast-moving CLIs that still rely on it.
- Add validation that executes `agent-browser` instead of only checking that the command exists.

**Non-Goals:**

- Changing Hermes browser configuration away from `local`.
- Replacing the wrapped Hermes doctor/runtime shims with a new integration model.
- Reworking the entire managed npm tooling design for all CLIs.
- Adding Chrome, Chromium, or a different browser backend to the image.

## Decisions

### Treat `agent-browser` as a Nix-managed exception in the user-tooling layer

The managed user-tooling script should stop installing `agent-browser` in the mutable npm project and stop linking `/home/hermes/.local/bin/agent-browser` to `node_modules/.bin/agent-browser`. Instead, the runtime should let `agent-browser` resolve from the image-managed Nix package already present on PATH.

Rationale:

- The live image already proves that the Nix-managed binary works on arm64.
- The failure is caused by the mutable npm path taking precedence over the working image path.
- This is the narrowest fix that restores behavior without changing Hermes configuration.

Alternatives considered:

- Keep the npm-managed path and patch the mutable install in place after `npm install`.
  Rejected because it keeps the broken source of truth in the hot path and adds more convergence complexity.
- Repackage the npm-installed binary inside the mutable project during boot.
  Rejected because it duplicates packaging logic that the image already owns successfully through Nix.
- Move every managed CLI from npm to Nix.
  Rejected because it is a broader toolchain-policy change than this bug requires.

### Preserve the Hermes doctor/runtime compatibility shims

The wrapped Hermes package should continue to satisfy doctor/runtime checks through PATH discovery and the packaged `node_modules/agent-browser` layout it already injects.

Rationale:

- The wrapper already changes doctor and tools-config checks to accept `shutil.which("agent-browser")` as sufficient.
- Keeping those shims intact avoids turning this bug fix into a broader Hermes integration change.

Alternatives considered:

- Remove the compatibility shims and depend only on one runtime path.
  Rejected because the current doctor contract already relies on the wrapper behavior and removing it would widen risk for no benefit.

### Validate execution, not just discovery

Image tests should execute `agent-browser --help` in addition to checking command discovery.

Rationale:

- `command -v` passed in the broken image because the bad shim existed on PATH.
- The failure mode is specifically below command discovery at native binary launch time.

Alternatives considered:

- Keep command discovery checks only.
  Rejected because it does not cover the observed regression.

## Risks / Trade-offs

- [Mutable tooling expectations still mention npm-managed `agent-browser`] → Update runtime documentation and tests to describe `agent-browser` as a supported Nix-managed exception while leaving `codex` and `opencode` npm-managed.
- [A stale persisted `/home/hermes/.local/bin/agent-browser` symlink could continue shadowing the fixed path after image replacement] → The convergence script should explicitly remove or rewrite any prior npm-rooted `agent-browser` symlink during boot/refresh.
- [Hermes browser flows could regress if PATH no longer exposes a working `agent-browser`] → Verify both `agent-browser --help` and a doctor/browser-path smoke test in image validation.
- [Future maintainers may accidentally re-add `agent-browser` to the npm-managed set] → Keep the requirement and tests explicit about execution and about the exception in the managed tooling contract.

## Migration Plan

1. Remove `agent-browser` from the managed npm package/bin sets in the user-tooling convergence logic.
2. Ensure convergence deletes any old `/home/hermes/.local/bin/agent-browser` symlink that points into the mutable npm project and rebinds it to the supported runtime path if needed.
3. Rebuild and boot the image.
4. Verify `agent-browser --help` succeeds in the running image and `hermes doctor` does not regress on the supported browser path.
5. If rollback is needed, restore the prior convergence script and image build, understanding that rollback also restores the arm64 startup failure.

## Open Questions

- Whether the implementation should create `/home/hermes/.local/bin/agent-browser` as an explicit symlink to the Nix-managed wrapper or rely on the existing PATH ordering to resolve the store binary without a home-local symlink.
