## Context

The live `ghostship-hermes` deployment on `chill-penguin-root` still fails to stop cleanly. During controlled restarts on `2026-04-12`, the host Podman unit sent `SIGTERM` to the container and then escalated to `SIGKILL` after the configured grace window. The failure reproduced under multiple budgets:

- the generated Podman container config still advertises `StopTimeout=10`, even though the host systemd unit itself allows `TimeoutStopSec=120`
- a direct `podman stop --time 30 hermes` still escalated to `SIGKILL` after 30 seconds

That establishes two things. First, the host-side `10s` stop budget is too short for this container shape. Second, increasing the grace period alone is not enough; some part of the inner shutdown path is still failing to complete within a materially larger window.

The same live image still emits repeatable stage-2 activation warnings:

- `could not create symlink /etc/hostname`
- `could not create symlink /etc/hosts`
- `ln: failed to create symbolic link '/root/.nix-defexpr/channels/channels': Read-only file system`

Those are not currently fatal, but they are real defects in the published image’s container-mode contract. The image metadata also remains sparse: the live image exposes title, description, and version labels, but not source or revision provenance.

The latest live boot also exposed a second operational drag in the startup path. `ghostship-hermes-user-tooling.service` took roughly 37 seconds wall time and 18.484 seconds CPU on `2026-04-12T10:14:30Z` to `10:15:07Z`, while repeatedly removing managed Nix profile entries one by one (`git`, `curl`, `jq`, `nix`, `ripgrep`, `fd`, `python3`, `uv`, `yq-go`, `tmux`, `nodejs_22`, `gh`, `openssh`, and `hermes-agent-wrapped`) before reconciling them again. That means the service currently pays a large convergence cost even on a normal boot where most managed state is already current.

This change therefore spans the image module, the publishable image metadata, and the image/runtime validation surface.

## Goals / Non-Goals

**Goals:**
- Make the published image exit cleanly on `SIGTERM` within the declared container stop budget during supported restart and stop flows.
- Align the repo-owned managed gateway stop behavior with the upstream Hermes service contract where that affects clean shutdown.
- Remove the current known container-mode boot warnings around Podman-managed `/etc` files and root channel seeding.
- Reduce boot-time tooling convergence work when the managed Nix profile and npm layer are already in the desired state.
- Extend validation so shutdown, activation cleanliness, and OCI provenance labels are all directly testable.
- Preserve the existing single-agent runtime topology and managed home/workspace contract.

**Non-Goals:**
- Redesign the full Hermes service graph or replace inner `systemd` with a different init model.
- Eliminate every boot-time log line from the image; this change targets the confirmed repeatable defects only.
- Rework the heavy startup path beyond what is necessary to validate shutdown and activation correctness.
- Change the existing published image name, tag semantics, or GHCR release channel policy.

## Decisions

### Fix the stop-path in the image first, then tune the host stop budget

The investigation shows that the container still fails to stop gracefully even with `30s`, so the primary defect is inside the image shutdown path rather than only in the host Podman unit. The implementation should therefore start by aligning the image-owned stop semantics with upstream Hermes expectations and then re-measure the required Podman stop timeout on the live host.

This specifically points at the managed gateway service definition in `packages/hermes-image/nixos-module.nix`, where the repo currently renders its own `hermes-gateway.service` without the full upstream stop fields. The image should explicitly render the intended kill mode, kill signal, and stop timeout instead of inheriting unrelated defaults.

Alternative considered: fix only the host by increasing the Podman stop timeout. Rejected because the container already failed under `30s`, so a host-only change would mask the image defect instead of repairing it.

### Treat container-mode activation noise as an image contract problem

The `/root/.nix-defexpr` warning comes from inherited NixOS channel setup behavior that does not fit this image. The image should disable that root channel seeding path rather than tolerate a known read-only write failure on every boot.

The `/etc/hostname` and `/etc/hosts` warnings split by ownership. Root channel seeding is still an image defect and should be disabled in the image module. The `/etc` warnings come from Podman injecting those files into the container while NixOS stage-2 still tries to materialize its own copies. Because the runtime contract keeps an explicit Nix hostname, the clean fix is a compatible container-mode ownership split: the image keeps `networking.hostName`, while the supported Podman deployment should pass `--no-hostname --no-hosts` so Podman uses the image-managed files instead of injecting conflicting ones.

Alternative considered: document the warnings as harmless and leave them in place. Rejected because they create noisy false signals during every boot and make real activation regressions harder to identify.

### Validate shutdown and provenance directly in image-focused checks

The runtime and publication contract should be enforced through direct evidence, not assumptions. The image validation path should exercise a real stop/restart flow and inspect the resulting host/container logs for forced-kill behavior, while metadata checks should assert the new OCI source and revision labels on the explicit publishable artifact.

Alternative considered: limit validation to local file inspection and existing smoke tests. Rejected because the current defect only reproduced clearly under real Podman stop behavior on the live host.

### Make managed user-tooling convergence incremental instead of destructive-by-default

The current `ghostship-hermes-user-tooling` implementation always removes matching managed profile entries and re-adds them, then rewrites `package.json` and reruns `npm install`, regardless of whether the managed state is already correct. That guarantees convergence, but it turns every normal boot into a full reconciliation pass.

The design should keep the same declared managed toolchain contract while switching the convergence algorithm to a diff-based update:

- compare the current managed profile entries to the declared spec and mutate only changed entries
- preserve stable entries rather than removing and re-adding them every boot
- avoid rerunning npm dependency installation when the declared npm package set has not changed
- continue to repair drift and stale managed symlinks when the runtime-owned state actually differs

Alternative considered: leave the current destructive reconciliation in place and rely only on the daily refresh timer. Rejected because the slow boot path is already materially affecting restart time on the live deployment.

## Risks / Trade-offs

- [Risk] Tightening the gateway stop contract could expose an upstream Hermes shutdown bug instead of fixing it locally. → Mitigation: align first with upstream service semantics, then isolate any remaining long-running shutdown path with targeted validation.
- [Risk] Disabling channel-related activation behavior could affect workflows that implicitly expect root `nix-channel` state. → Mitigation: keep the repo’s documented flake/Nix workflow intact and validate that supported `nix` usage inside the image still works without root channel seeding.
- [Risk] Suppressing `/etc/hostname` and `/etc/hosts` activation writes could conflict with expectations elsewhere in the NixOS container profile. → Mitigation: scope the change to the published container deployment shape and validate a normal Podman boot after the adjustment.
- [Risk] Live stop-path validation can be slower and more operationally heavy than local smoke tests. → Mitigation: keep the new validation narrowly focused on restart/stop correctness and metadata inspection rather than broadening it into a full redeploy suite.
- [Risk] Making tooling convergence incremental could let stale managed entries survive if the diff logic is incomplete. → Mitigation: keep one explicit drift-repair path in validation and ensure the reconciler still removes entries that are managed but no longer declared.

## Migration Plan

1. Update the image module so the managed gateway service renders explicit graceful-stop settings, the container-mode activation path no longer attempts the known invalid writes, and the tooling reconciler avoids unnecessary full-profile churn on boot.
2. Extend image-focused validation to assert:
   - the image exposes the new OCI provenance labels
   - the image avoids destructive no-op tooling convergence on a steady-state boot
   - the image exits cleanly under the supported stop signal contract
   - the supported Podman runtime contract (`--no-hostname --no-hosts`) removes the known `/etc` activation warnings while preserving the image-managed hostname
3. Rebuild and publish the image.
4. Re-test the live host with a controlled `podman-hermes.service` restart and a direct `podman stop` flow.
5. If graceful stop still requires a larger host budget after the image fixes, update the host Podman deployment to use the measured stop timeout instead of the current 10-second container setting.

Rollback is straightforward: redeploy the prior image and restore the prior host stop-timeout setting if the new graceful-stop path introduces regressions.

## Open Questions

- Which inner unit is still the dominant shutdown blocker after the gateway stop fields are aligned: the gateway itself, the user manager, or another system service in the container?
- Should the repo enforce the final Podman stop timeout entirely in generated container metadata, in the host unit, or in both places for defense in depth?
- Do we want the image validation to fail on any matching activation warning text, or should the check target the three currently known defects only?
