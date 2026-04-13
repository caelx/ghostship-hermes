## 1. Host Runtime Contract

- [x] 1.1 Locate the authoritative `podman-hermes.service` source and update it to preserve the supported container stop contract, including a successful clean signal-exit path.
- [x] 1.2 Update the supported deployment/runtime wiring so the image-managed hostname contract does not conflict with host-injected `/etc/hostname` state.
- [x] 1.3 Validate on `chill-penguin` that `systemctl stop` and `systemctl restart` complete without `SIGKILL` escalation and without leaving `podman-hermes.service` failed.

## 2. Activation Cleanliness

- [x] 2.1 Remove the remaining root channel artifacts or generation path that cause stage-2 `channels` warnings and read-only `/root/.nix-defexpr` writes.
- [x] 2.2 Extend image or deployment validation to check the latest boot window for the supported hostname and root-channel cleanliness expectations.
- [x] 2.3 Validate on the deployed host that the latest Hermes boot no longer logs the supported `/etc/hostname` or root-channel warnings.

## 3. Managed Tooling Convergence

- [x] 3.1 Replace the destructive managed user-tooling refresh loop with actual-state diffing for managed Nix profile entries, npm install state, and managed shims.
- [x] 3.2 Add verification coverage for both a steady-state no-op rerun and a targeted single-drift repair.
- [x] 3.3 Normalize default Nix profile priority handling so omitted declared priorities do not force a remove-and-readd cycle against live entries that report the default installed priority.
- [ ] 3.4 Validate on `chill-penguin` that an immediate rerun of `ghostship-hermes-user-tooling.service` no longer removes and re-adds the full managed profile and skips unnecessary npm work.
