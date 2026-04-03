## 1. Persistence layout and boot migration

- [ ] 1.1 Change the image/runtime contract to keep `HERMES_HOME=/opt/data`, `HOME=/home/hermes`, and use `/opt/data` as the canonical persistent Hermes volume.
- [ ] 1.2 Add the `/opt/data/home` facade and implement boot-time copy-missing migration plus symlink repair for the managed home directories.
- [ ] 1.3 Add `/workspace` as a separate persisted work volume and expose it into the user home as a normal workspace path.
- [ ] 1.4 Support persisted `/nix` for Nix-installed tools and build outputs, and document a safe mount strategy that does not rely on an empty Docker volume over `/nix`.

## 2. Runtime and Hermes-native behavior

- [ ] 2.1 Rework the `systemd` runtime and user-manager bootstrap so persisted user units live under the symlinked home facade.
- [ ] 2.2 Keep the custom Ghostship Hermes dashboard stack and related system services working under the `systemd` runtime after the persistence-layout change.
- [ ] 2.3 Keep Hermes-native profile behavior and `hermes gateway install` working under the new layout, including persistence for named profiles and wrapper commands.
- [ ] 2.4 Ensure the runtime remains non-root in normal operation and does not install or require `sudo`.

## 3. Seeding and updater re-rooting

- [ ] 3.1 Re-root workstation seeding into `/opt/data` and `/opt/data/home`, with copy-if-missing semantics for repo-managed defaults.
- [ ] 3.2 Re-root app installs, updater state, mutable asset refresh, and generated config into the persisted layout without clobbering existing volume data.
- [ ] 3.3 Keep app and asset refresh failure-tolerant so the last working local state remains active after any failed update.

## 4. Documentation and validation

- [ ] 4.1 Rewrite the README, changelog, and runtime guidance around the `/opt/data`-first Hermes-native workstation model.
- [ ] 4.2 Add local Docker validation that proves reused `/opt/data` preserves default Hermes state, named profiles, and HOME-anchored config under the symlinked facade.
- [ ] 4.3 Add local Docker validation that proves reused `/workspace` preserves work items and that reused `/nix` preserves Nix-installed tools or build outputs with the documented safe mount strategy.
- [ ] 4.4 Verify the final proposal, design, specs, docs, and validation steps all match the new persistence contract before implementation continues.
