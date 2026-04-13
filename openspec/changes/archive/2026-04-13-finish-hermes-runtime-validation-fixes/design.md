## Context

The latest live validation on `chill-penguin` narrowed the follow-up scope significantly. The deployed image now stops cleanly through the host-managed Podman unit, the host unit no longer reports a normal signaled stop as failed, and the latest boot is clean for the `/etc/hostname`, root-channel, and read-only `/root/.nix-defexpr` warnings that originally motivated this change.

The remaining problem is isolated to `ghostship-hermes-user-tooling.service`. The deployed image already contains the new `ref_matches_entry()` logic, and the live `nix profile list --json` output now matches the expected `originalUrl = flake:nixpkgs` plus `attrPath = legacyPackages.<system>.<name>` shape. Even so, an immediate rerun still removes and re-adds every managed entry. Live inspection shows why: most declared managed entries omit an explicit priority, so the desired side normalizes to `None`, while the live installed entries report priority `5`. The current keep-existing check still requires `current_priority == desired_priority`, which treats the default priority as drift on every rerun.

## Goals / Non-Goals

**Goals:**
- Preserve the already-validated host-side Podman contract and activation-cleanliness behavior as the supported deployment model.
- Eliminate the remaining false-positive drift path in `ghostship-hermes-user-tooling.service`.
- Make a second managed-tooling run after convergence a true no-op for both managed profile entries and npm tooling.
- Extend validation so the live host check catches the default-priority mismatch before release.

**Non-Goals:**
- Re-open the previously fixed host stop-signal, success-exit, or hostname wiring work unless a new live regression appears.
- Redesign the overall Hermes boot topology or replace inner `systemd` with a different init model.
- Optimize image pull or broader startup latency beyond what is needed to validate managed-tooling convergence.

## Decisions

### Host runtime behavior remains part of the supported container contract
The change keeps the host Podman unit in scope because live validation proved those settings are necessary and now correct. The supported contract remains: preserve the image stop signal, avoid conflicting hostname injection, and treat the expected signal-exit path as a successful systemd unit result.

Alternatives considered:
- Remove the host runtime behavior from the change now that it is fixed. Rejected because the spec still needs to capture the supported deployment contract that was validated on the live host.

### Managed tooling convergence must treat omitted declared priority as the stable default
The remaining convergence defect is not source-ref matching anymore. The implementation must treat a missing declared priority as compatible with the live default installed priority when the ref and entry identity already match. Only an explicit declared priority should force a priority comparison and mutation.

Alternatives considered:
- Force explicit priority declarations for every managed entry. Rejected because it bloats the declaration surface and still leaves the underlying default-priority semantics implicit.
- Ignore priority entirely. Rejected because explicitly managed priorities such as the Python environment ordering still matter and must still be enforceable.

### Live validation must cover the default-priority no-op case directly
The existing validation direction remains correct, but it needs one sharper assertion: a live rerun after convergence must not remove entries whose only difference is that the desired declaration omits an explicit priority while the installed profile reports the default priority.

Alternatives considered:
- Rely on local smoke tests only. Rejected because the bug survived into a deployed image even after the first round of convergence fixes.

## Risks / Trade-offs

- [Treating omitted priority as stable default could hide a real priority regression] → Only skip the priority comparison when the desired declaration omits a priority; keep enforcing explicitly declared priorities such as the Python precedence override.
- [Live validation may still miss a provider-specific Nix profile shape] → Validate against the actual `nix profile list --json` shape seen on the deployed target and keep the check in the host-facing validator.
- [The host contract could drift again outside this repo] → Keep the deployment contract documented in spec and validation even though the authoritative host module lives in external config.

## Migration Plan

1. Update the managed-tooling spec and tasks to capture the default-priority false-positive drift path.
2. Adjust the convergence logic so omitted declared priorities are compatible with the live default installed priority while explicit priorities still enforce ordering.
3. Rebuild and redeploy the image to `chill-penguin`.
4. Re-run the live validator, focusing on the immediate `ghostship-hermes-user-tooling.service` rerun and targeted drift repair.

## Open Questions

- Do we want the live validator to assert a specific upper bound for no-op tooling reruns, or is “no removal churn and no npm install work” the stronger contract?
