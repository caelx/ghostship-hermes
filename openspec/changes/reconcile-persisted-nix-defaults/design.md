## Context

The current workstation image already uses Nix in two distinct ways:

- the image build resolves baseline helper utilities such as `bw`, `gws`, `gh`, `gcloud`, and `blogtato` from Nix
- the running workstation exposes persisted `/nix` so Hermes or downstream operators can install additional userland packages that survive container replacement

Today those two lanes are coupled too loosely. The final image stage resolves baseline tools to concrete `/nix/store/...` paths at build time and creates `/opt/ghostship/bin/*` symlinks to those store objects. The boot sequence only seeds `/nix` when the mounted path is empty. On a reused non-empty `/nix` mount, the image upgrades but the persisted store does not automatically gain the new build's expected objects, so the shipped helper symlinks become broken.

This design must preserve the current high-level image structure:

- `ubuntu:24.04` base image
- Hermes core in `/opt/hermes`
- router in `/opt/ghostship-router`
- persisted `/home/hermes`, `/workspace`, and `/nix`
- optional user-managed Nix installs surviving replacement

The change therefore needs to fit the existing image/runtime model instead of introducing a separate package manager or abandoning persisted `/nix`.

## Goals / Non-Goals

**Goals:**
- Keep the current workstation image contract where baseline helper tools are shipped by the image.
- Make reused non-empty `/nix` mounts a supported upgrade path for those shipped helper tools.
- Separate image-managed Nix defaults from user-managed Nix installs so the runtime can refresh the baseline without deleting downstream additions.
- Keep boot reconciliation offline and deterministic by shipping the needed Nix closure with the image.
- Preserve operator overrides by keeping user profile paths separate from the image-managed default profile.

**Non-Goals:**
- Replacing persisted `/nix` with an immutable-only tool layer.
- Reverting `bw`, `gws`, `gh`, or `gcloud` to downstream-only manual installs.
- Running `nix profile install` against the network during every container boot.
- Garbage-collecting user-managed `/nix` content automatically on every start.

## Decisions

### Decision: Ship one image-managed Nix default profile instead of direct store symlinks

The image will stop treating baseline Nix tools as individual `/opt/ghostship/bin -> /nix/store/...` symlinks. Instead, the build will create a single image-managed Nix profile/closure for the guaranteed helper set and export that closure into the image as boot-importable state.

Why:
- one profile gives the runtime a stable rebind point across upgrades
- the runtime can detect whether the expected generation is present in persisted `/nix`
- a single managed profile path on `PATH` is easier to validate than many raw store symlinks

Alternative considered:
- keep direct store symlinks and reseed `/nix` wholesale on every boot
- rejected because it is fragile, harder to make idempotent with reused mounts, and risks overwriting user-managed store content

### Decision: Reconcile the managed default profile on every boot

The cont-init phase will keep the current “seed `/nix` if empty” behavior, but it will add a second idempotent step for non-empty `/nix` mounts:

1. detect the image-managed default profile generation expected by this image
2. if the target store path/profile is missing from persisted `/nix`, import the shipped closure into `/nix`
3. atomically update the managed default profile symlink/generation pointer

Why:
- fresh mounts still bootstrap cleanly
- existing mounts receive the image's required defaults without erasing user data
- this directly addresses the current live failure mode on `chill-penguin`

Alternative considered:
- never reconcile at boot and require operators to run a manual `nix profile install` repair command after every image upgrade
- rejected because the image is already claiming these tools are part of the shipped workstation contract

### Decision: Separate image-managed and user-managed Nix paths

The runtime will expose two Nix-backed paths:

- an image-managed default profile for the guaranteed helper set
- the existing user profile (`/home/hermes/.nix-profile/bin`) for operator/Hermes-installed extras

The managed profile will be placed on `PATH` separately from the user profile so the contract is explicit.

Why:
- baseline availability can be reconciled safely
- user-installed tools remain durable and operator-controlled
- user profile overrides remain possible if the user intentionally installs a newer binary

Alternative considered:
- merge the baseline tool set into the user's profile
- rejected because the image should not mutate operator-managed profile generations behind their back

### Decision: Export the image-managed closure as part of the existing second image phase

The current image already has a second phase that installs Ghostship-specific runtime content and utility wiring. This change will extend that phase to:

- build the baseline Nix default profile
- export the closure/profile metadata into `/opt/ghostship`
- install a small boot reconciler that restores the profile into persisted `/nix`

Why:
- this matches the current image layering
- the base image can remain cacheable and Ghostship-free
- the profile export belongs with the Ghostship-managed utility layer, not the immutable upstream-Hermes base layer

Alternative considered:
- move all Nix-managed default tools into the base image phase
- rejected because it weakens the current two-phase build split and reduces cache reuse for the true Hermes base layer

## Risks / Trade-offs

- **Managed profile drift vs user expectations** → Document clearly that the image-managed default profile is refreshed by image upgrades, while the user profile remains separately operator-owned.
- **Boot-time complexity** → Keep reconciliation narrow: import closure if missing, update managed profile pointer, do not perform aggressive GC or network fetches.
- **Store growth over time** → Leave GC/manual cleanup as a documented maintenance task rather than an automatic boot behavior.
- **Spec churn across tool-specific runtime specs** → Update the tool-specific specs in the same change so docs and tests stop disagreeing about whether these tools are shipped.

## Migration Plan

1. Extend the image build to export the baseline default-tool closure/profile into `/opt/ghostship`.
2. Update cont-init to reconcile that managed profile into persisted `/nix` on every boot.
3. Update `PATH` and smoke validation to resolve baseline tools through the managed profile instead of raw store symlinks.
4. Update docs to explain fresh `/nix` seeding, reused `/nix` reconciliation, and the split between image-managed defaults and user-managed Nix installs.
5. Roll forward by redeploying the new image on top of existing persisted `/nix`; the boot reconciler should repair missing default tools automatically.
6. Roll back by redeploying the prior image; existing user-managed `/nix` state remains intact because the reconciler only adds the managed closure/profile and does not delete user data.

## Open Questions

- Whether the managed default profile should precede or follow the user profile on `PATH`; the current recommendation is user profile first, managed defaults second.
- Whether `blogtato` should remain in the managed Nix default set or move to a different image-managed layer if its packaging becomes unstable.
