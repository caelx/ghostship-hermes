## 1. Runtime Rebuild

- [x] 1.1 Remove the remaining legacy workstation payloads from the repo and image wiring.
- [x] 1.2 Keep Hermes declarative through the upstream NixOS module.
- [x] 1.3 Change the persistence contract to persisted `/home/hermes`, `/workspace`, and `/nix`.
- [x] 1.4 Keep the dedicated `hermes` identity at `3000:3000`.

## 2. Dashboard

- [x] 2.1 Keep the minimal dashboard and old Hermes logo.
- [x] 2.2 Ensure `Open Terminal` creates a focused new left-rail tab.
- [x] 2.3 Ensure `Close Terminal` removes the active tab and returns to the blank homepage when no sessions remain.
- [x] 2.4 Ensure terminals start in `/home/hermes`.

## 3. Profiles And Hermes Layout

- [x] 3.1 Bootstrap `test` and `coder` from NixOS-managed startup.
- [x] 3.2 Document the `/home/hermes/.hermes` layout and how the profiles are stored.
- [x] 3.3 Document the systemd unit graph and call out any deviation from upstream.

## 4. Validation

- [x] 4.1 Build the x86_64 image successfully.
- [x] 4.2 Run the dashboard smoke test.
- [x] 4.3 Run the full persistence test against reused `/home/hermes`, `/workspace`, and `/nix`.
- [x] 4.4 Verify `nix profile install` persistence.
- [x] 4.5 Verify later-installed tool state persistence.
- [x] 4.6 Leave a final container running for manual dashboard inspection.

## 5. Cleanup

- [x] 5.1 Update README, CHANGELOG, AGENTS, and the active OpenSpec docs.
- [x] 5.2 Aggressively prune stale Docker images, containers, build artifacts, and unused volumes, leaving at most one retained copy of each needed image.
