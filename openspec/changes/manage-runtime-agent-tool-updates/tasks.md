## 1. Live-image validation first

- [ ] 1.1 Move Hermes and the stable user-facing CLI set into updateable user-managed state on the live image
- [ ] 1.1a Verify `nix-daemon.socket` is active in the live container before attempting any user-profile installs or upgrades
- [ ] 1.2 Install the in-scope npm CLIs on the live image where Hermes expects them
- [ ] 1.3 Add the Home Assistant dependency support on the live image
- [ ] 1.4 Reduce Hermes doctor warnings on the live image for supported features only
- [ ] 1.5 Confirm with the user that the resulting live-image behavior is correct
- [ ] 1.6 Align ttyd to the dashboard's blue theme tokens on the live image and validate the result with the user

## 2. Backport the minimum-system-viable runtime contract

- [ ] 2.1 Shrink the image-owned system package set to the minimum viable boot/supervision surface
- [ ] 2.2 Add a user-profile bootstrap/update contract for Hermes, `git`, `curl`, `jq`, `python3`, `nix`, `ripgrep`, and `node`/`npm`
- [ ] 2.3 Add a persisted npm prefix/cache contract for the fast-moving agent CLIs under `/home/hermes`
- [ ] 2.4 Add boot-time update ordering so the user profile and npm layer are ready before profile gateways start
- [ ] 2.4a Make the in-container Nix daemon/socket part of that boot-time ordering contract
- [ ] 2.5 Add a persistent daily updater for user-profile packages and npm-managed CLIs

## 3. Supported doctor cleanup and Home Assistant support

- [ ] 3.1 Wire the in-scope shared env vars needed to reduce Hermes doctor noise for actual runtime features
- [ ] 3.2 Keep per-profile auth/model flows Hermes-native and verify the runtime no longer depends on copied auth files
- [ ] 3.3 Decide and package the validated Home Assistant dependency set in the correct layer
- [ ] 3.4 Document which doctor warnings remain intentionally out of scope

## 4. Dashboard visual backport

- [ ] 4.1 Backport the validated ttyd blue-theme token alignment into the repo dashboard/runtime contract

## 5. Publish the codified image

- [ ] 5.1 Update runtime documentation to describe the minimum-system-viable layered contract
- [ ] 5.2 Update changelog and any affected repo guidance that still assumes user-facing tools belong in the immutable image layer
- [ ] 5.3 Build and push the new image after the backported contract matches the validated live image
