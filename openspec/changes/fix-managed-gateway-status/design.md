## Context

The live `ghostship-hermes` runtime already keeps the dashboard, router, and per-profile gateway services healthy through repo-owned systemd units such as `ghostship-hermes-profile-assistant.service`. The current operator problem is not that the gateways are down; it is that interactive Hermes CLI commands do not share the same managed-runtime view as the running services.

Today the managed units set `HERMES_MANAGED=true` in their service environment, but interactive shells only see the root managed marker under `/home/hermes/.hermes/.managed`. When an operator runs `hermes -p <profile> gateway ...`, Hermes resolves `HERMES_HOME` to `/home/hermes/.hermes/profiles/<profile>` and no longer sees the managed marker. The upstream CLI then falls back to user-service assumptions such as `hermes-gateway-<profile>.service`, `systemctl --user`, and linger guidance, even though this repo intentionally uses system-level `ghostship-hermes-profile-*` units.

This is cross-cutting because the fix touches bootstrap/runtime state, the wrapped Hermes CLI behavior, and the validation contract for operator diagnostics.

## Goals / Non-Goals

**Goals:**

- Make managed-mode detection consistent for the root Hermes home and every managed profile home.
- Make `gateway status` report the actual repo-managed gateway state instead of false negatives.
- Make gateway control commands for managed profiles either target the repo-owned units correctly or fail with explicit managed-runtime guidance instead of upstream user-service instructions.
- Add validation coverage so this mismatch does not regress silently in future image updates.

**Non-Goals:**

- Replacing the repo-managed per-profile systemd topology with upstream `hermes gateway install`.
- Reworking the dashboard, router, or Discord runtime behavior outside the operator control-plane mismatch.
- Eliminating every optional `doctor` warning unrelated to the managed gateway contract.

## Decisions

### 1. Write managed markers into each managed profile root

The bootstrap path should place `.managed` in each managed profile directory, not only the root Hermes home.

Rationale:

- This matches upstream Hermes' documented managed-shell contract, which checks for `.managed` in the active `HERMES_HOME`.
- It keeps profile-scoped interactive invocations in managed mode even when the operator targets `hermes -p assistant`, `hermes -p operations`, or `hermes -p supervisor`.
- It is low-risk because the repo already treats those profile roots as Nix-managed scaffolded state.

Alternative considered: export `HERMES_MANAGED=true` globally for all interactive shells. Rejected because it is broader than needed and makes local/manual debugging less explicit than a profile-local marker.

### 2. Patch the wrapped Hermes gateway CLI for the managed image topology

The wrapped Hermes package should patch the upstream gateway command path so the managed image does not rely on upstream `hermes-gateway*` service names for status and control.

Rationale:

- Adding `.managed` markers alone will not fix `status`, `start`, `stop`, or `restart`, because those code paths still look for upstream user or system services.
- The repo already patches the wrapped Hermes package for runtime-specific doctor/tooling behavior, so extending the wrapper for this managed-runtime seam keeps the divergence explicit and centralized.
- The managed image has stable repo-owned unit names and profile metadata, so the wrapper can resolve the correct service identity deterministically.

Alternative considered: switch the image back to upstream `hermes gateway install` services. Rejected because the repo intentionally manages one persistent gateway service per declarative profile and uses that topology across bootstrap, dashboard metadata, and systemd ordering.

### 3. Distinguish profile-scoped control from root-scoped summary behavior

Named profile gateway commands should target the matching managed profile unit, while root-scoped gateway commands should provide managed guidance or summary output instead of pretending there is one upstream root gateway service.

Rationale:

- The managed image runs profile gateways, not a single root messaging gateway.
- `hermes gateway status` at the root home should not report a managed profile process as a "manual" foreground gateway.
- `hermes gateway start|stop|restart` at the root home is ambiguous in this image and should not silently operate on the wrong unit.

Alternative considered: map all root gateway commands to the default profile. Rejected because it hides the repo's explicit multi-profile topology and can surprise operators.

### 4. Validate the managed control-plane paths explicitly

The runtime validation path should exercise `hermes -p <profile> doctor` and `hermes -p <profile> gateway status`, plus at least one managed control-path behavior check.

Rationale:

- The current bug survived because service health and dashboard reachability were tested, but operator-facing control-path behavior was not.
- The intended contract is partly diagnostic and ergonomic, so direct CLI validation is the right place to lock it down.

Alternative considered: rely only on unit tests in the wrapped Hermes package. Rejected because the bug manifested in the built image/runtime integration, not only in isolated Python logic.

## Risks / Trade-offs

- [Risk] Additional wrapper patching increases the repo's divergence from upstream Hermes. → Mitigation: keep the patch narrow, document why it exists, and align it to upstream managed-mode semantics where possible.
- [Risk] Root-scoped gateway behavior may still be surprising if operators expect a single gateway. → Mitigation: make the CLI output explicitly describe the managed multi-profile model and direct operators to profile-scoped commands.
- [Risk] Managed markers in profile directories could be mistaken for Hermes-owned mutable state. → Mitigation: treat them as generated bootstrap artifacts alongside the existing root `.managed` marker and validate their presence after bootstrap.

## Migration Plan

1. Update bootstrap to materialize `.managed` in the root Hermes home and each managed profile root.
2. Patch the wrapped Hermes gateway CLI to recognize the managed image topology for status and control flows.
3. Add or update validation to cover managed profile `doctor` and `gateway status` behavior.
4. Rebuild the image, verify locally, then verify on a live container deployment before release.

Rollback is straightforward: revert the bootstrap and wrapper changes, rebuild the image, and redeploy the previous behavior. This would restore the current misleading CLI behavior but should not disrupt running gateway services.

## Open Questions

- Should root-scoped `hermes gateway status` list all managed profile gateways, only the default profile, or both a default and a full profile summary?
- For managed profile `start|stop|restart`, should the wrapper invoke `systemctl` directly against the repo-owned unit, or should it refuse and direct operators to `systemctl` for mutation while still fixing `status`?
