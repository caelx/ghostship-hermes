## Context

Live validation on `chill-penguin` showed that the previously deployed image picked up the new OCI labels, `SIGRTMIN+3` container stop signal, and upstream-aligned gateway stop semantics, but the rollout is still not fully healthy. A normal `systemctl stop podman-hermes.service` now stops the container without Podman escalating to `SIGKILL`, yet the host unit still lands in `failed` because the Podman process exits `130` after the clean signaled shutdown. The same deployment still logs a conflicting `/etc/hostname` setup warning, still exposes root-channel state that causes stage-2 `channels` warnings and a read-only `/root/.nix-defexpr` write attempt, and still spends roughly 34-37 seconds in `ghostship-hermes-user-tooling.service` on every run.

The remaining work crosses the image, runtime validation, and host deployment boundary. The image alone can advertise the intended stop signal and disable channel support, but the live deployment still needs a host runtime contract that does not reintroduce conflicting hostname files or treat the expected signal-exit path as a service failure. The user-tooling problem is separate: it is a convergence algorithm defect, not just a slow cold-start.

## Goals / Non-Goals

**Goals:**
- Define and validate the supported host-side Podman contract for the Hermes image.
- Eliminate the remaining stage-2 root-channel and hostname warning path from supported deployments.
- Make `ghostship-hermes-user-tooling.service` truly incremental so a second run after convergence is effectively a no-op.
- Extend validation so future rollouts prove stop semantics, activation cleanliness, and steady-state tooling behavior on the deployed host.

**Non-Goals:**
- Redesign the overall Hermes boot topology or replace inner `systemd` with a different init model.
- Optimize image pull or `/srv/apps/hermes/nix` refresh latency beyond what is needed to validate convergence behavior.
- Change the approved mutable helper CLI set or broader managed-agent contract outside the convergence bug being fixed.

## Decisions

### Host runtime behavior becomes part of the supported container contract
The follow-up change will treat the host Podman unit as part of the runtime contract, not as an implementation detail outside the image. The contract must preserve the image's declared stop semantics, avoid conflicting `/etc/hostname` injection when the image keeps `networking.hostName`, and map the expected Podman exit status for a clean signaled stop to a successful systemd unit result.

Alternatives considered:
- Rely on image metadata alone. Rejected because the live deployment already proved that the image can advertise `SIGRTMIN+3` while the host unit still reports normal stops as failures and still injects a conflicting hostname file.
- Remove the explicit hostname from the image. Rejected because the runtime contract intentionally keeps `networking.hostName = "ghostship-hermes"`.

### Root channel state must be removed from the immutable image/runtime path, not merely disabled in config
The container should be treated as a flake-oriented Nix runtime with no root channel contract. The design will remove or suppress the persisted root channel links that currently survive into the booted image so stage-2 no longer reports disabled-but-present channels or attempts to write `/root/.nix-defexpr/channels/channels` on a read-only root filesystem.

Alternatives considered:
- Accept the warning as harmless. Rejected because it is a real image defect and it makes runtime validation noisy.
- Hide the warning in tests only. Rejected because the live container still carries contradictory root channel state that should not be present.

### Managed tooling convergence will compare desired state to actual installed state before mutating
The user-tooling service must stop treating every run as a rebuild. The implementation should compute the desired managed profile and npm/bin state, inspect the current state, and mutate only entries that are missing, stale, or no longer managed. A second run immediately after convergence must skip both destructive `nix profile remove` churn and `npm install` when nothing changed.

Alternatives considered:
- Keep the current remove-and-readd loop and only optimize logging. Rejected because the observed cost is real work and remains operationally heavy on every boot.
- Compare only entry names. Rejected because profile entry names alone are not a sufficiently strong identity for all managed sources; the comparison should use the actual installed source metadata or an equivalent manifest.

### Validation must exercise the deployed runtime, not only the source tree
This change will require a live or image-loaded validation flow that checks `systemctl stop`/`restart`, boot warnings in the latest start window, and a second `ghostship-hermes-user-tooling.service` run after convergence. Source changes are not enough; the live deployment already demonstrated that some expected fixes did not reach the running artifact.

Alternatives considered:
- Rely on unit tests or container-local smoke tests alone. Rejected because the failures were visible only in the live host unit and persisted-home runtime behavior.

## Risks / Trade-offs

- [Host deployment config may live outside this repo] → Capture the required host-unit contract in spec and validation, and update whichever deployment source actually owns `podman-hermes.service`.
- [Removing root channel artifacts could affect undocumented root workflows] → Keep the supported contract explicit that Hermes runs as the non-root `hermes` user and that root channels are not part of the image surface.
- [No-op tooling convergence could miss real drift] → Compare canonical managed source identities and add a targeted drift-repair scenario to validation.
- [Tight live validation can be slower or more operationally invasive] → Keep the checks narrowly scoped to stop/start behavior, latest boot logs, and one extra tooling rerun.

## Migration Plan

1. Update the runtime specs and docs to define the supported host-unit flags, success exit status handling, activation cleanliness expectations, and managed-tooling convergence rules.
2. Implement the host/runtime and image changes, then rebuild and redeploy the image to `chill-penguin`.
3. Validate one clean `systemctl stop` plus `systemctl start`, one clean `systemctl restart`, the latest boot warnings, and a steady-state tooling rerun.
4. Roll back by restoring the previous host-unit/runtime flags or image revision if the new deployment regresses startup or gateway liveness.

## Open Questions

- Is the authoritative `podman-hermes.service` definition maintained in this repo's deployment code or in an external host configuration repo/runbook?
- Should the host runtime contract standardize only `--no-hostname`, or should it also explicitly set other Podman file-injection flags even when current logs no longer show `/etc/hosts` noise?
