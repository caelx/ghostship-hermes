## Why

Live validation on `chill-penguin` now shows that the host runtime contract and container activation cleanliness fixes are working: normal `systemctl stop` and `restart` no longer hit Podman `SIGKILL`, the host unit no longer lands in `failed`, and the latest boot is clean for the `/etc/hostname`, root-channel, and `/root/.nix-defexpr` warnings that previously polluted stage-2.

One live defect remains: `ghostship-hermes-user-tooling.service` still removes and re-adds the full managed Nix profile on an immediate rerun even though the deployed image already contains the new source-ref matching logic. The remaining mismatch is narrower than the original proposal expected: the convergence code still treats the live default profile priority (`5`) as drift whenever the declared managed entry omits an explicit priority.

## What Changes

- Keep the validated host Podman runtime contract and activation-cleanliness requirements in scope as proven behavior for supported deployments.
- Tighten managed user-tooling convergence so an omitted declared priority is treated as the stable default priority instead of forcing a remove-and-readd cycle on every rerun.
- Extend validation to prove the deployed runtime contract directly, including a no-op managed tooling rerun against a live host after convergence.

## Capabilities

### New Capabilities
- `container-runtime-contract`: Defines the supported host-managed Podman and activation contract for the Hermes container, including clean service-stop behavior, supported hostname/hosts wiring, and container boot cleanliness expectations.

### Modified Capabilities
- `managed-runtime-tooling`: Tightens the managed tooling contract so steady-state convergence is no-op by default and only repairs actual drift, including the default-priority case for managed Nix profile entries.

## Impact

Affected areas include the managed user-tooling convergence logic, image validation scripts, and the runtime contract documentation for `podman-hermes.service`. Operators keep the cleaner supported host/runtime contract that is already validated on `chill-penguin`, while the remaining work focuses on eliminating the last false-positive drift path in managed tooling convergence.
