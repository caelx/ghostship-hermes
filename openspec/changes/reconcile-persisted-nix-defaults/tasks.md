## 1. Build the managed Nix default profile

- [x] 1.1 Change the image utility build so the baseline Nix-backed helper set is produced as one managed default profile/closure instead of raw `/opt/ghostship/bin -> /nix/store/...` symlinks.
- [x] 1.2 Export the managed default profile payload and generation metadata into `/opt/ghostship` during the Ghostship-specific image phase.
- [x] 1.3 Update the runtime `PATH` contract so baseline Nix-backed helper tools resolve through the managed default profile while user-managed Nix installs remain on a separate profile path.

## 2. Reconcile persisted `/nix` on boot

- [x] 2.1 Extend `10-ghostship-prepare` to detect the image-managed default profile expected by the current image and import it into persisted `/nix` when missing.
- [x] 2.2 Make the reconciliation idempotent for both empty and reused non-empty `/nix` mounts without overwriting unrelated user-managed Nix content.
- [x] 2.3 Remove or replace any remaining runtime assumptions that baseline helper tools are available through direct build-time `/nix/store/...` symlinks.

## 3. Validate upgrade and runtime behavior

- [x] 3.1 Update the smoke test to execute baseline managed Nix helper commands after first boot, restart, and full container replacement with a reused `/nix`.
- [x] 3.2 Add focused validation for the repaired live failure mode where `bw`, `gws`, `gh`, `gcloud`, or `blogtato` would otherwise exist only as broken symlinks.
- [x] 3.3 Validate the new behavior against a reused persisted `/nix` deployment path such as `chill-penguin`.

## 4. Document the new `/nix` contract

- [x] 4.1 Update workstation docs and README to explain the managed Nix default profile, the user-managed Nix profile, and the supported reuse flow for existing non-empty `/nix` mounts.
- [x] 4.2 Update the tool-specific runtime docs/spec-linked guidance for `bw`, `gh`, `gcloud`, and `gws` so they match the shipped image-managed baseline.
- [x] 4.3 Document how this design fits the current two-phase image build: base Hermes/system layer first, Ghostship utility/profile export second.
- [x] 4.4 Keep the embedded `Terminal` tab patched in after `Keys`, as the final upstream dashboard tab.
