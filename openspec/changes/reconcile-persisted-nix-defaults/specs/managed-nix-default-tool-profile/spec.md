## ADDED Requirements

### Requirement: Workstation exports an image-managed Nix default-tool profile
The workstation image SHALL export a deterministic Nix closure/profile for the baseline helper-tool set that the image guarantees, and that exported profile SHALL be consumable by the boot runtime without requiring a network fetch.

#### Scenario: Image contains the managed default profile payload
- **WHEN** maintainers inspect a built workstation image
- **THEN** the image contains an exported payload for the managed Nix default-tool profile
- **AND** that payload identifies the baseline helper-tool generation expected by the image

### Requirement: Boot reconciles the managed default profile into persisted `/nix`
The workstation boot sequence SHALL reconcile the image-managed Nix default-tool profile into the mounted persisted `/nix` on every start, including when `/nix` is already non-empty from a prior image generation.

#### Scenario: Empty `/nix` receives the managed default profile
- **WHEN** the workstation starts with an empty persisted `/nix`
- **THEN** boot seeds `/nix` with the required store contents
- **AND** boot installs or activates the managed default profile expected by the image

#### Scenario: Reused `/nix` mount receives missing managed defaults
- **WHEN** the workstation starts with a reused non-empty persisted `/nix`
- **AND** the image-managed default profile expected by the image is missing from that mount
- **THEN** boot imports the missing managed profile payload into persisted `/nix`
- **AND** boot activates the image-managed default profile without deleting unrelated user-managed Nix content

### Requirement: Managed defaults and user-managed Nix installs remain separate
The workstation SHALL keep the image-managed Nix default-tool profile logically separate from the Hermes-user Nix profile so the image can refresh its guaranteed helper set without taking ownership of user-managed profile generations.

#### Scenario: User-managed Nix packages survive managed profile refresh
- **WHEN** boot reconciles the image-managed default profile on a persisted `/nix` that already contains user-managed Nix installs
- **THEN** the runtime preserves those user-managed installs
- **AND** the runtime does not replace the Hermes-user profile solely to refresh the image-managed default profile

### Requirement: Baseline helper tools resolve from the managed Nix profile
The workstation SHALL expose the guaranteed baseline Nix-backed helper tools through the reconciled managed Nix default profile rather than through raw symlinks to build-time `/nix/store/...` paths.

#### Scenario: Baseline helper tools remain callable after image replacement
- **WHEN** a workstation container is replaced with a newer image while reusing the same persisted `/nix`
- **THEN** guaranteed baseline helper tools such as `bw`, `gws`, `gh`, `gcloud`, and `blogtato` resolve on the Hermes-user `PATH`
- **AND** those commands do not fail only because a stale raw `/nix/store/...` symlink points to a missing store path
