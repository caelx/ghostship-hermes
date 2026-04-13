## Why

Live validation on `chill-penguin` proved the earlier runtime-contract repair only landed partially. The deployed image now stops on `SIGRTMIN+3` without hitting Podman `SIGKILL`, but normal `systemctl stop` still leaves the host unit failed, stage-2 still logs `/etc/hostname` and root-channel warnings, and `ghostship-hermes-user-tooling.service` still burns ~34-37 seconds re-removing the same managed profile entries on every run.

## What Changes

- Define the supported host Podman runtime contract for Hermes so clean signaled container stops are treated as successful service stops and the deployment passes the runtime flags required by the image contract.
- Remove the remaining container stage-2 root-channel activation noise instead of leaving `/nix/var/nix/profiles/per-user/root/channels` and `/root/.nix-defexpr` in a contradictory disabled-but-still-referenced state.
- Make managed user-tooling convergence actually incremental on steady-state boots and reruns so already-converged managed profile entries and npm tooling are left in place.
- Extend validation to prove the deployed runtime contract directly: clean stop semantics, expected activation cleanliness, and a cheap no-op user-tooling rerun.

## Capabilities

### New Capabilities
- `container-runtime-contract`: Defines the supported host-managed Podman and activation contract for the Hermes container, including clean service-stop behavior, supported hostname/hosts wiring, and container boot cleanliness expectations.

### Modified Capabilities
- `managed-runtime-tooling`: Tightens the managed tooling contract so steady-state convergence is no-op by default and only repairs actual drift.

## Impact

Affected areas include the Hermes image module, managed user-tooling convergence logic, image validation scripts, and the deployment/runtime contract for `podman-hermes.service` on live hosts. Operators gain a clearer supported runtime contract for deploying and validating the image, and rollouts stop masking partial regressions behind "healthy enough" starts.
